#!/usr/bin/env python3
import asyncio
import logging
import struct
import time
import io
from asyncio.subprocess import PIPE
from typing import Dict, Set
from fastapi import WebSocket
from PIL import Image

logger = logging.getLogger("BroadcastSystem.CameraManager")

class DownstreamChannelBroker:
    """각 슬롯(채널)별 실시간 바이너리 프레임 브로드캐스터"""
    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        req_proto = websocket.headers.get('sec-websocket-protocol')
        chosen = None
        if req_proto:
            try:
                protos = [p.strip() for p in req_proto.split(',') if p.strip()]
                if 'camera-stream' in protos:
                    chosen = 'camera-stream'
            except Exception:
                pass
        try:
            if chosen: 
                await websocket.accept(subprotocol=chosen)
            else: 
                raise RuntimeError(f"[Camera Stream Connect] 서브 프로토콜 불일치")
        except Exception:
            raise RuntimeError(f"[Camera Stream Connect] 카메라 스트림 채널 연결 실패")
        
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_binary(self, data: bytes):
        if not self.active_connections:
            return
        disconnected_clients = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_bytes(data)
            except Exception:
                disconnected_clients.add(connection)
        for client in disconnected_clients:
            self.disconnect(client)


class CameraStreamManager:
    """RTSP 스트림 유실 감지 및 자동 재연결(Auto-Reconnect)을 전담하는 매니저"""
    def __init__(self):
        self.live_brokers: Dict[int, DownstreamChannelBroker] = {}
        self.stream_tasks: Dict[int, asyncio.Task] = {}
        self.stream_procs: Dict[int, asyncio.subprocess.Process] = {}
        self.keep_alive_flags: Dict[int, bool] = {}  # 슬롯별 모니터링 활성화 플래그

    async def start_rtsp_stream(self, slot: int, url: str, username: str = None, password: str = None):
        # 기존 모니터링 및 프로세스 자원 완벽히 청소
        self.keep_alive_flags[slot] = False
        await self.stop_rtsp_stream(slot)
        
        if slot not in self.live_brokers:
            self.live_brokers[slot] = DownstreamChannelBroker(channel_name=f"Live-Slot-{slot}")

        # 자가 치유 메인 루프 가동
        self.keep_alive_flags[slot] = True
        self.stream_tasks[slot] = asyncio.create_task(
            self._rtsp_supervisor_loop(slot, url, username, password)
        )

    async def _rtsp_supervisor_loop(self, slot: int, url: str, username: str, password: str):
        """FFmpeg가 다운되거나 멈추면 3초 대기 후 무한 재연결을 시도하는 감시 루프"""
        input_url = url
        if username and password and ("@" not in url.split("//", 1)[-1]):
            parts = url.split("//", 1)
            if len(parts) == 2:
                input_url = f"{parts[0]}//{username}:{password}@{parts[1]}"

        broker = self.live_brokers[slot]

        while self.keep_alive_flags.get(slot, False):
            logger.info(f"[Slot {slot}] RTSP 스트림 프로세스를 시작합니다.")
            
            # 🌟 무조건 정상 작동하던 최초의 표준 명령어로 완벽하게 회귀
            cmd = [
                "ffmpeg", 
                "-rtsp_transport", "tcp",
                "-i", input_url,
                "-an", "-c:v", "mjpeg", "-q:v", "5",
                "-f", "mpjpeg", "-"
            ]

            proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
            self.stream_procs[slot] = proc

            # FFmpeg 내부 분석 메시지를 실시간으로 추적하는 서브 리더 태스크
            async def _stderr_logger_worker():
                try:
                    while True:
                        line = await proc.stderr.readline()
                        if not line:
                            break
                        logger.debug(f"[FFmpeg 로그 Slot {slot}]: {line.decode('utf-8', errors='ignore').strip()}")
                except Exception:
                    pass

            stderr_task = asyncio.create_task(_stderr_logger_worker())

            buffer = bytearray()
            try:
                while self.keep_alive_flags.get(slot, False):
                    try:
                        # 7초 동안 아무 데이터도 들어오지 않으면 파이썬 측에서 감지하고 프로세스 재생성 트리거
                        chunk = await asyncio.wait_for(proc.stdout.read(32768), timeout=7.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"[Slot {slot}] 데이터 수신 타임아웃! FFmpeg 프로세스를 재시작합니다.")
                        break

                    if not chunk:
                        logger.warning(f"[Slot {slot}] FFmpeg가 스트림 출력을 중단했습니다.")
                        break
                    
                    buffer.extend(chunk)

                    while True:
                        if len(buffer) < 4:
                            break

                        start_idx = buffer.find(b"\xFF\xD8")
                        if start_idx == -1:
                            buffer.clear()
                            break

                        if start_idx > 0:
                            del buffer[:start_idx]
                            start_idx = 0

                        end_idx = buffer.find(b"\xFF\xD9", start_idx)
                        if end_idx == -1:
                            break

                        # 깨짐 없는 온전한 한 프레임 적출
                        jpeg_len = end_idx + 2
                        image_payload = bytes(buffer[:jpeg_len])
                        del buffer[:jpeg_len]

                        # 디버깅용 온전한 JPG 실시간 로컬 디스크 스냅샷 저장
                        try:
                            with Image.open(io.BytesIO(image_payload)) as img:
                                img.save("./last_frame.jpg", "JPEG")
                        except Exception as file_err:
                            logger.debug(f"[디버그] 프레임 조립 중 일시적 유실 패스: {file_err}")

                        # 프론트엔드와 사전 약속된 24바이트 프로토콜 헤더 패킹
                        magic = 0x7a
                        type_byte = (2 << 4) | (3 & 0x0f)
                        now = time.time()
                        pts_sec = int(now)
                        pts_usec = int((now - pts_sec) * 1_000_000)

                        header = struct.pack(
                            ">BBBBIIIII",
                            magic, type_byte, 0, 0,
                            0, 0, len(image_payload), pts_sec, pts_usec
                        )

                        await broker.broadcast_binary(header + image_payload)

            except Exception as e:
                logger.error(f"[Slot {slot}] 스트림 파싱 에러 발생: {e}")
            finally:
                # 자원 해제 및 감시단 태스크 수거
                stderr_task.cancel()
                try: 
                    proc.kill()
                    await proc.wait()
                except Exception: 
                    pass
                
                if self.keep_alive_flags.get(slot, False):
                    logger.info(f"[Slot {slot}] 3초 후 스트림 복구를 시도합니다...")
                    await asyncio.sleep(3.0)

    async def stop_rtsp_stream(self, slot: int):
        self.keep_alive_flags[slot] = False
        proc = self.stream_procs.pop(slot, None)
        if proc:
            try: 
                proc.kill()
                await proc.wait()
            except Exception: 
                pass
        task = self.stream_tasks.pop(slot, None)
        if task:
            task.cancel()

    async def stop_all(self):
        for slot in list(self.stream_procs.keys()):
            await self.stop_rtsp_stream(slot)