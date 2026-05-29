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

    async def start_rtsp_stream(
        self, slot: int, url: str, username: str = None, password: str = None
    ):
        """[외부 호출용] 특정 슬롯(채널)의 RTSP 스트리밍 및 감시 루프를 시작합니다."""
        self.keep_alive_flags[slot] = False
        await self.stop_rtsp_stream(slot)

        if slot not in self.live_brokers:
            self.live_brokers[slot] = DownstreamChannelBroker(
                channel_name=f"Live-Slot-{slot}"
            )

        # 자가 치유 감시 루프 백그라운드 가동
        self.keep_alive_flags[slot] = True
        self.stream_tasks[slot] = asyncio.create_task(
            self._rtsp_supervisor_loop(slot, url, username, password)
        )

    async def _rtsp_supervisor_loop(
        self, slot: int, url: str, username: str, password: str
    ):
        """[감시자] FFmpeg 프로세스를 실행하고, 꺼지면 3초 후 무한 재연결을 시도하는 메인 루프"""
        input_url = self._build_auth_url(url, username, password)
        broker = self.live_brokers[slot]

        while self.keep_alive_flags.get(slot, False):
            logger.info(f"[Slot {slot}] RTSP 스트림 프로세스를 시작합니다.")

            # 1. FFmpeg 프로세스 실행
            proc = await self._start_ffmpeg_process(input_url)
            self.stream_procs[slot] = proc

            # 2. FFmpeg 에러/로그 실시간 수집기 가동
            stderr_task = asyncio.create_task(
                self._ffmpeg_logger_worker(slot, proc)
            )

            # 3. 데이터 수신 및 브로드캐스트 처리
            try:
                await self._stream_processing_loop(slot, proc, broker)
            except Exception as e:
                logger.error(f"[Slot {slot}] 스트림 처리 중 에러 발생: {e}")
            finally:
                # 4. 프로세스 종료 및 자원 정리
                stderr_task.cancel()
                await self._kill_process(proc)

                # 복구 대기
                if self.keep_alive_flags.get(slot, False):
                    logger.info(
                        f"[Slot {slot}] 3초 후 스트림 복구를 시도합니다..."
                    )
                    await asyncio.sleep(3.0)

    def _build_auth_url(
        self, url: str, username: str, password: str
    ) -> str:
        """RTSP URL에 인증 정보(ID/PW)를 안전하게 삽입합니다."""
        if username and password and ("@" not in url.split("//", 1)[-1]):
            parts = url.split("//", 1)
            if len(parts) == 2:
                return f"{parts[0]}//{username}:{password}@{parts[1]}"
        return url

    async def _start_ffmpeg_process(
        self, input_url: str
    ) -> asyncio.subprocess.Process:
        """FFmpeg 명령어를 조립하여 프로세스를 실행합니다."""
        cmd = [
            "ffmpeg",
            "-rtsp_transport",
            "tcp",
            "-i",
            input_url,
            "-an",
            "-c:v",
            "mjpeg",
            "-q:v",
            "5",
            "-f",
            "mpjpeg",
            "-",
        ]
        return await asyncio.create_subprocess_exec(
            *cmd, stdout=PIPE, stderr=PIPE
        )

    async def _ffmpeg_logger_worker(
        self, slot: int, proc: asyncio.subprocess.Process
    ):
        """FFmpeg 내부 분석 메시지(stderr)를 실시간으로 콘솔에 기록합니다."""
        try:
            while True:
                line = await proc.stderr.readline()
                if not line:
                    break
                logger.debug(
                    f"[FFmpeg 로그 Slot {slot}]: {line.decode('utf-8', errors='ignore').strip()}"
                )
        except Exception:
            pass

    async def _stream_processing_loop(
        self,
        slot: int,
        proc: asyncio.subprocess.Process,
        broker: DownstreamChannelBroker,
    ):
        """FFmpeg 출력에서 바이트 데이터를 읽어 프레임을 조립하고 전송합니다."""
        buffer = bytearray()

        while self.keep_alive_flags.get(slot, False):
            try:
                # 7초 동안 데이터가 없으면 타임아웃 발생 (카메라 먹통 감지)
                chunk = await asyncio.wait_for(
                    proc.stdout.read(32768), timeout=7.0
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"[Slot {slot}] 데이터 수신 타임아웃! FFmpeg 프로세스를 재시작합니다."
                )
                break

            if not chunk:
                logger.warning(
                    f"[Slot {slot}] FFmpeg가 스트림 출력을 중단했습니다."
                )
                break

            buffer.extend(chunk)
            # 버퍼에서 온전한 JPG 이미지를 찾아서 추출 및 전송
            await self._parse_and_broadcast_frames(slot, buffer, broker)

    async def _parse_and_broadcast_frames(
        self, slot: int, buffer: bytearray, broker: DownstreamChannelBroker
    ):
        """바이트 버퍼를 파싱하여 완벽한 JPG 프레임을 추출하고 웹소켓으로 방송합니다."""
        while True:
            if len(buffer) < 4:
                break

            # JPEG 시작 지점 획득
            start_idx = buffer.find(b"\xFF\xD8")
            if start_idx == -1:
                buffer.clear()
                break

            if start_idx > 0:
                del buffer[:start_idx]
                start_idx = 0

            # JPEG 끝 지점 획득
            end_idx = buffer.find(b"\xFF\xD9", start_idx)
            if end_idx == -1:
                break

            # 온전한 이미지 한 장 잘라내기
            jpeg_len = end_idx + 2
            image_payload = bytes(buffer[:jpeg_len])
            del buffer[:jpeg_len]

            # (선택) 디버깅용 실시간 스냅샷 저장
            self._save_debug_snapshot(image_payload)

            # 웹소켓 통신 규격용 24바이트 헤더 조립
            header = self._create_protocol_header(len(image_payload))

            # 웹소켓 브로커를 통해 대기 중인 모든 클라이언트에게 전송
            await broker.broadcast_binary(header + image_payload)

    def _save_debug_snapshot(self, image_payload: bytes):
        """가장 최근 프레임을 디스크에 로컬 이미지 파일로 저장합니다."""
        try:
            with Image.open(io.BytesIO(image_payload)) as img:
                img.save("./last_frame.jpg", "JPEG")
        except Exception as file_err:
            logger.debug(
                f"[디버그] 프레임 조립 중 일시적 유실 패스: {file_err}"
            )

    def _create_protocol_header(self, payload_len: int) -> bytes:
        """프론트엔드와 수신 약속된 고유의 24바이트 바이너리 헤더를 생성합니다."""
        magic = 0x7a
        type_byte = (2 << 4) | (3 & 0x0f)  # 프로토콜 상의 약속된 타입 값 비트 연산
        now = time.time()
        pts_sec = int(now)
        pts_usec = int((now - pts_sec) * 1_000_000)

        # 빅 엔디안(>) 포맷으로 패킹
        return struct.pack(
            ">BBBBIIIII",
            magic,
            type_byte,
            0,
            0,
            0,
            0,
            payload_len,
            pts_sec,
            pts_usec,
        )

    async def _kill_process(self, proc: asyncio.subprocess.Process):
        """안전하게 서브 프로세스를 강제 종료하고 자원을 반환합니다."""
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass

    async def stop_rtsp_stream(self, slot: int):
        """[외부 호출용] 특정 슬롯의 모니터링 플래그를 끄고 모든 자원을 해제합니다."""
        self.keep_alive_flags[slot] = False

        proc = self.stream_procs.pop(slot, None)
        await self._kill_process(proc)

        task = self.stream_tasks.pop(slot, None)
        if task:
            task.cancel()

    async def stop_all(self):
        """[외부 호출용] 관리 중인 모든 슬롯의 스트리밍을 한 번에 정지합니다."""
        for slot in list(self.stream_procs.keys()):
            await self.stop_rtsp_stream(slot)