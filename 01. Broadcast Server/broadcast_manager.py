#!/usr/bin/env python3
import asyncio
from collections import deque
import struct
import time
from asyncio.subprocess import PIPE
import json
import logging
from pathlib import Path
from typing import Dict, List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.utils.message_utils import MessageUtils

# 시스템 표준 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BroadcastSystem")


# =====================================================================
# [PART 1] 데이터 파싱 클래스 (Parser) - 오직 변환만 담당
# =====================================================================
from src.MessageParser.message_parser import MessageParser
from src.CameraManager.rtsp_streamer import DownstreamChannelBroker


# =====================================================================
# [PART 2] Upstream connection classes (externalized)
# =====================================================================
from src.UpstreamManager.base import BaseConnection
from src.UpstreamManager.pure_ws import PureWebSocketConnection
from src.UpstreamManager.http_auth_ws import HttpAuthWebSocketConnection
from src.UpstreamManager.connection_manager import (
    build_hub_connection,
    build_va_connection,
    send_connected_hubs_to_web,
    send_connected_vas_to_web
)

# ⭐️ [새로 만든 카메라 전담 모듈 가져오기]
from src.CameraManager.rtsp_streamer import CameraStreamManager

# =====================================================================
# Global Variables
# =====================================================================
ROBOT_CORE_WEB_SYSTEM_ID = 500  # 시스템 ID 상수 정의 (예시값)


# =====================================================================
# [PART 3] 다운스트림 채널 브로커 (Downstream Channels)
# =====================================================================
class DownstreamChannelBroker:
    """오직 들어온 완제품 메시지를 클라이언트에게 전송(방송)하는 역할만 전담"""

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        req_proto = websocket.headers.get('sec-websocket-protocol')
        chosen = None
        if req_proto:
            try:
                protos = [p.strip() for p in req_proto.split(',') if p.strip()]
                if 'stream' in protos:
                    chosen = 'stream'
            except Exception:
                protos = []

        try:
            if chosen:
                await websocket.accept(subprotocol=chosen)
            else:
                await websocket.accept()
        except Exception as e:
            logger.warning(f"[{self.channel_name}] websocket.accept error: {e}")
            try:
                await websocket.accept()
            except Exception:
                pass

        self.active_connections.add(websocket)
        client = getattr(websocket, 'client', None)
        client_str = f"{client[0]}:{client[1]}" if client else "unknown"
        logger.info(f"[{self.channel_name}] 웹 클라이언트 접속 완료 from {client_str} subproto={chosen or 'none'} (현재 접속자: {len(self.active_connections)}명)")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client = getattr(websocket, 'client', None)
            client_str = f"{client[0]}:{client[1]}" if client else "unknown"
            logger.info(f"[{self.channel_name}] 웹 클라이언트 접속 종료 from {client_str} (현재 접속자: {len(self.active_connections)}명)")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected_clients = set()
        
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected_clients.add(connection)

        for client in disconnected_clients:
            self.disconnect(client)


# =====================================================================
# [SYSTEM INTEGRATION] 메시지 수집/분배/중계 아키텍처 (Orchestrator)
# =====================================================================
class BroadcastManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.upstream_tasks: List[asyncio.Task] = []
        self.upstreams: List[BaseConnection] = []
        
        # 1. 오리지널 로봇 데이터 채널 브로커 유지
        self.telemetry_broker = DownstreamChannelBroker(channel_name="Telemetry")
        self.events_broker = DownstreamChannelBroker(channel_name="Events")
        self.control_broker = DownstreamChannelBroker(channel_name="Control")
        
        # ⭐️ [카메라 스트림 전담 모듈 컴포지션 결합]
        self.camera_manager = CameraStreamManager()
        # 서버 단에서 관리하는 카메라 스트림 재시도 설정 (기본값)
        self.camera_retry_attempts = 3
        
        self.saved_server_entries: List[dict] = []

        # 오리지널 질문자님의 아키텍처 철학 독립 큐 유지
        self.raw_message_queue = asyncio.Queue()     
        self.parsed_message_queue = asyncio.Queue()  

        self.worker_tasks: List[asyncio.Task] = []
        self.va_tokens: Dict[str, str] = {}

    def load_config(self) -> list:
        p = Path(self.config_path)
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            logger.error(f"설정 파일 로딩 실패: {e}")
            return []

    # 🏃‍♂️ 오리지널 백그라운드 독립 일꾼 1: 파싱 전담 유지
    async def _message_parser_worker(self):
        logger.info("[Parser Worker] 가동 시작 - 원시 메시지 파싱 전담")
        while True:
            try:
                source_name, raw_msg = await self.raw_message_queue.get()
                parsed = MessageParser.parse_and_route(source_name, raw_msg)
                if parsed:
                    await self.parsed_message_queue.put(parsed)
                self.raw_message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Parser Worker] 에러 발생: {e}")

    # 🏃‍♂️ 오리지널 백그라운드 독립 일꾼 2: 재전송/분배 전담 유지
    async def _message_delivery_worker(self):
        logger.info("[Delivery Worker] 가동 시작 - 파싱된 메시지 목적지 배송 전담")
        while True:
            try:
                parsed_msg = await self.parsed_message_queue.get()
                target = parsed_msg.pop("target_channel", "telemetry")

                if target == "events":
                    await self.events_broker.broadcast(parsed_msg)
                else:
                    await self.telemetry_broker.broadcast(parsed_msg)
                    
                self.parsed_message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Delivery Worker] 에러 발생: {e}")

    async def start(self):
        self.saved_server_entries = self.load_config()
        self.worker_tasks.append(asyncio.create_task(self._message_parser_worker()))
        self.worker_tasks.append(asyncio.create_task(self._message_delivery_worker()))
        logger.info(f"설정 로드 완료 및 역할별 파이프라인 일꾼 워커(Parser/Delivery) 가동 완료.")

    async def stop(self):
        for conn in self.upstreams:
            conn.stop()
        for task in self.upstream_tasks:
            task.cancel()
        for task in self.worker_tasks:
            task.cancel()
            
        # ⭐️ [카메라 서브 모듈 자원 일괄 중단]
        await self.camera_manager.stop_all()
            
        await asyncio.gather(*self.upstream_tasks, *self.worker_tasks, return_exceptions=True)


# =====================================================================
# FastAPI App 구동 엔드포인트 설정
# =====================================================================
app = FastAPI(title="Patrol Robot Downstream Broker System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = BroadcastManager(config_path="servers.json")

@app.on_event("startup")
async def startup_event():
    await manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    await manager.stop()


# --- 오리지널 비즈니스 제어 채널 엔드포인트 완벽 유지 ---
@app.websocket("/ws/robots/telemetry")
async def telemetry_endpoint(websocket: WebSocket):
    await manager.telemetry_broker.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.telemetry_broker.disconnect(websocket)
    except Exception as e:
        logger.error(f"Telemetry 통신 예외 에러: {e}")
        manager.telemetry_broker.disconnect(websocket)


@app.websocket("/ws/robots/events")
async def events_endpoint(websocket: WebSocket):
    await manager.events_broker.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.events_broker.disconnect(websocket)
    except Exception as e:
        logger.error(f"Events 통신 예외 에러: {e}")
        manager.events_broker.disconnect(websocket)

@app.websocket("/ws/control")
async def control_endpoint(websocket: WebSocket):
    await manager.control_broker.connect(websocket)
    await send_connected_hubs_to_web(websocket, manager)
    await send_connected_vas_to_web(websocket, manager)
        
    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            if data.get('type') == 'robot_hub_connect':
                handshake_header = MessageUtils.make_header(type_="handshake", protocol_source="ui", protocol_category="request")
                handshake_payload = {"systemid": ROBOT_CORE_WEB_SYSTEM_ID }
                handshake_data = { "header": handshake_header, "payload": handshake_payload }
                data['handshake'] = handshake_data
                conn = build_hub_connection(data, manager)
                if conn is not None:
                    task = asyncio.create_task(conn.run_loop())
                    manager.upstream_tasks.append(task)

            if data.get('type') == 'va_engine_connect':
                conn = build_va_connection(data, manager)
                if conn is not None:
                    task = asyncio.create_task(conn.run_loop())
                    manager.upstream_tasks.append(task)
                
    except WebSocketDisconnect:
        manager.control_broker.disconnect(websocket)
    except Exception as e:
        logger.error(f"Control 채널 통신 예외 에러: {e}")
        manager.control_broker.disconnect(websocket)


# =====================================================================
# 🎥 콤포지션 이식: 개편된 전담 카메라 컨트롤 및 비디오 라우팅 스트림 채널
# =====================================================================
@app.websocket("/ws/camera_control")
async def camera_control_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                msg = await websocket.receive_text()
            except RuntimeError as re:
                logger.warning(f"Camera control socket not connected or accept missing: {re}")
                break
            try:
                data = json.loads(msg)
            except Exception:
                continue

            print(f"[Camera] 카메라 rtsp 스트림 연결 시도 : {data}")

            action = data.get("type")
            if action == "camera_connect":
                url = data.get("url")
                username = data.get("username")
                password = data.get("password")
                slot = data.get("slot")

                # 슬롯 지정 누락 시 사용 가능한 슬롯(0~5) 찾아서 자동 매핑
                if slot is None:
                    for i in range(6):
                        if i not in manager.camera_manager.stream_tasks:
                            slot = i
                            break
                    if slot is None: slot = 0

                try:
                    # 신규 카메라 전담 모듈 가동 트리거 및 최초 프레임 검증(서버 측)
                    # 재시도 횟수는 BroadcastManager에서 관리하는 값을 사용합니다.
                    await manager.camera_manager.start_rtsp_stream(slot, url, username, password)

                    stream_url = f"ws://localhost:8000/ws/live?ch={slot}"

                    print(f"[Camera] 카메라 스트림 연결 성공 (Slot {slot}) - 클라이언트에게 스트림 URL 전송: {stream_url}")
                    await websocket.send_text(json.dumps({
                        "type": "camera_connected",
                        "slot": slot,
                        "streamUrl": stream_url
                    }))
                except Exception as e:
                    logger.error(f"카메라 모듈 가동 실패 (Slot {slot}): {e}")
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "camera_connect_fail",
                            "slot": slot,
                            "reason": str(e)
                        }))
                    except Exception:
                        pass
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/live")
async def live_endpoint(websocket: WebSocket):
    params = websocket.query_params
    print(f"Live Endpoint 접속 시도 with params: {params}")
    ch = params.get('ch', '0')
    try:
        ch_idx = int(ch)
    except Exception:
        ch_idx = 0

    broker = manager.camera_manager.live_brokers[ch_idx]
    await broker.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broker.disconnect(websocket)
    except Exception as e:
        logger.error(f"Live 바이너리 엔드포인트 통신 장애 (Slot {ch_idx}): {e}")
        broker.disconnect(websocket)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)