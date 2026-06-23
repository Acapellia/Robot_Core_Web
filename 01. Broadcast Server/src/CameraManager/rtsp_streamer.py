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

# FFmpeg stderr에서 중요 키워드를 발견하면 WARNING 이상으로 올려서 출력
_FFMPEG_WARN_KEYWORDS = ("error", "failed", "invalid", "corrupt", "drop", "timeout", "refused", "connection")
_FFMPEG_ERROR_KEYWORDS = ("no route", "connection refused", "no such file", "permission denied")

class DownstreamChannelBroker:
    """각 슬롯(채널)별 실시간 바이너리 프레임 브로드캐스터"""
    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.active_connections: Set[WebSocket] = set()
        self._broadcast_fail_count = 0

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
        client = getattr(websocket, 'client', None)
        client_str = f"{client[0]}:{client[1]}" if client else "unknown"
        logger.info(
            f"[{self.channel_name}] 웹 클라이언트 접속 from {client_str} "
            f"(현재 접속자: {len(self.active_connections)}명)"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client = getattr(websocket, 'client', None)
            client_str = f"{client[0]}:{client[1]}" if client else "unknown"
            logger.info(
                f"[{self.channel_name}] 웹 클라이언트 접속 종료 from {client_str} "
                f"(현재 접속자: {len(self.active_connections)}명)"
            )

    async def broadcast_binary(self, data: bytes):
        if not self.active_connections:
            return
        connections = list(self.active_connections)

        # 느린 클라이언트 하나가 전체 루프를 블로킹하지 않도록 병렬 전송
        results = await asyncio.gather(
            *[conn.send_bytes(data) for conn in connections],
            return_exceptions=True
        )

        for conn, result in zip(connections, results):
            if isinstance(result, Exception):
                self._broadcast_fail_count += 1
                client = getattr(conn, 'client', None)
                client_str = f"{client[0]}:{client[1]}" if client else "unknown"
                logger.warning(
                    f"[{self.channel_name}] 클라이언트 {client_str} 전송 실패 "
                    f"(총 누적 실패: {self._broadcast_fail_count}회): {result}"
                )
                self.disconnect(conn)


class CameraStreamManager:
    """RTSP 스트림 유실 감지 및 자동 재연결(Auto-Reconnect)을 전담하는 매니저"""

    def __init__(self):
        self.live_brokers: Dict[int, DownstreamChannelBroker] = {}
        self.stream_tasks: Dict[int, asyncio.Task] = {}
        self.stream_procs: Dict[int, asyncio.subprocess.Process] = {}
        self.keep_alive_flags: Dict[int, bool] = {}  # 슬롯별 모니터링 활성화 플래그
        # 진단용 통계 카운터 (슬롯별)
        self._frame_counts: Dict[int, int] = {}
        self._broadcast_counts: Dict[int, int] = {}
        self._reconnect_counts: Dict[int, int] = {}
        self._last_stat_time: Dict[int, float] = {}
        self._last_frame_time: Dict[int, float] = {}

    async def start_rtsp_stream(
        self, slot: int, url: str, username: str = None, password: str = None
    ):
        """[외부 호출용] 특정 슬롯(채널)의 RTSP 스트리밍 및 감시 루프를 시작합니다."""
        # stop_rtsp_stream 안에서 flag를 끄므로 여기서 미리 끄지 않는다.
        # 미리 끄면 기존 supervisor의 finally 블록이 flag=False를 보고 재시작을 포기하는 race condition 발생.
        await self.stop_rtsp_stream(slot)

        if slot not in self.live_brokers:
            self.live_brokers[slot] = DownstreamChannelBroker(
                channel_name=f"Live-Slot-{slot}"
            )

        # 진단 카운터 초기화
        self._frame_counts[slot] = 0
        self._broadcast_counts[slot] = 0
        self._reconnect_counts[slot] = 0
        self._last_stat_time[slot] = time.time()
        self._last_frame_time[slot] = time.time()

        logger.info(f"[Slot {slot}] RTSP 스트림 시작 요청 - URL: {url}")

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
            attempt = self._reconnect_counts.get(slot, 0) + 1
            self._reconnect_counts[slot] = attempt
            logger.info(
                f"[Slot {slot}] RTSP 스트림 프로세스를 시작합니다. "
                f"(재연결 횟수: {attempt}회, 접속 클라이언트: {len(broker.active_connections)}명)"
            )

            # 1. FFmpeg 프로세스 실행
            proc = await self._start_ffmpeg_process(input_url)
            self.stream_procs[slot] = proc
            logger.info(f"[Slot {slot}] FFmpeg 프로세스 시작됨 (PID: {proc.pid})")

            # 2. FFmpeg 에러/로그 실시간 수집기 가동
            stderr_task = asyncio.create_task(
                self._ffmpeg_logger_worker(slot, proc)
            )

            # 3. 데이터 수신 및 브로드캐스트 처리
            loop_start = time.time()
            try:
                await self._stream_processing_loop(slot, proc, broker)
            except Exception as e:
                logger.error(f"[Slot {slot}] 스트림 처리 중 에러 발생: {e}", exc_info=True)
            finally:
                elapsed = time.time() - loop_start
                frames = self._frame_counts.get(slot, 0)
                logger.warning(
                    f"[Slot {slot}] 스트림 루프 종료 - "
                    f"운영 시간: {elapsed:.1f}초, 수신 프레임: {frames}장, "
                    f"FFmpeg PID: {proc.pid}, returncode: {proc.returncode}"
                )
                # 4. 프로세스 종료 및 자원 정리
                stderr_task.cancel()
                await self._kill_process(proc)

                # 복구 대기
                if self.keep_alive_flags.get(slot, False):
                    logger.info(f"[Slot {slot}] 3초 후 스트림 복구를 시도합니다...")
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
            "-timeout",
            "5",  # TCP 모드에서 접속 및 세션 유지 통합 타임아웃 (5초)
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
                text = line.decode('utf-8', errors='ignore').strip()
                if not text:
                    continue
                text_lower = text.lower()
                if any(kw in text_lower for kw in _FFMPEG_ERROR_KEYWORDS):
                    logger.error(f"[FFmpeg Slot {slot}] {text}")
                elif any(kw in text_lower for kw in _FFMPEG_WARN_KEYWORDS):
                    logger.warning(f"[FFmpeg Slot {slot}] {text}")
                else:
                    logger.debug(f"[FFmpeg Slot {slot}] {text}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"[FFmpeg Slot {slot}] stderr 수집 종료: {e}")

    async def _stream_processing_loop(
        self,
        slot: int,
        proc: asyncio.subprocess.Process,
        broker: DownstreamChannelBroker,
    ):
        """FFmpeg 출력에서 바이트 데이터를 읽어 프레임을 조립하고 전송합니다."""
        buffer = bytearray()
        self._frame_counts[slot] = 0
        self._last_stat_time[slot] = time.time()
        self._last_frame_time[slot] = time.time()
        stat_interval = 10.0  # 10초마다 수신 통계 출력

        while self.keep_alive_flags.get(slot, False):
            try:
                # 7초 동안 데이터가 없으면 타임아웃 발생 (카메라 먹통 감지)
                chunk = await asyncio.wait_for(
                    proc.stdout.read(32768), timeout=7.0
                )
            except asyncio.TimeoutError:
                idle = time.time() - self._last_frame_time.get(slot, time.time())
                logger.warning(
                    f"[Slot {slot}] 데이터 수신 타임아웃! "
                    f"마지막 프레임으로부터 {idle:.1f}초 경과. FFmpeg 재시작합니다."
                )
                break

            if not chunk:
                logger.warning(
                    f"[Slot {slot}] FFmpeg가 스트림 출력을 중단했습니다 (EOF). "
                    f"총 수신 프레임: {self._frame_counts.get(slot, 0)}장"
                )
                break

            buffer.extend(chunk)
            # 버퍼에서 온전한 JPG 이미지를 찾아서 추출 및 전송
            await self._parse_and_broadcast_frames(slot, buffer, broker)

            # 주기적 통계 로그
            now = time.time()
            elapsed = now - self._last_stat_time.get(slot, now)
            if elapsed >= stat_interval:
                frames = self._frame_counts.get(slot, 0)
                fps = frames / elapsed if elapsed > 0 else 0
                clients = len(broker.active_connections)
                logger.info(
                    f"[Slot {slot}] [통계] FPS: {fps:.1f}, "
                    f"수신 프레임(구간): {frames}장, "
                    f"접속 클라이언트: {clients}명, "
                    f"버퍼 크기: {len(buffer)}bytes"
                )
                self._frame_counts[slot] = 0
                self._last_stat_time[slot] = now

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
                logger.debug(f"[Slot {slot}] 버퍼에서 JPEG 시작 마커를 찾지 못해 버퍼를 초기화합니다. (버퍼 크기: {len(buffer)}bytes)")
                buffer.clear()
                break

            if start_idx > 0:
                logger.debug(f"[Slot {slot}] JPEG 시작 전 불필요 데이터 {start_idx}bytes 제거")
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

            self._frame_counts[slot] = self._frame_counts.get(slot, 0) + 1
            self._last_frame_time[slot] = time.time()

            # (선택) 디버깅용 실시간 스냅샷 저장
            # self._save_debug_snapshot(image_payload)

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