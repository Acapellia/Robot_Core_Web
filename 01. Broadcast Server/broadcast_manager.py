#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import time
import random
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 시스템 표준 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BroadcastSystem")


# =====================================================================
# [PART 1] 데이터 분류 및 파싱 파트 (Message Router & Parser)
# =====================================================================
class MessageParser:
    """수신된 데이터의 파싱 및 도메인(채널) 분류를 담당"""
    
    @staticmethod
    def parse_and_route(source_name: str, raw_message: str) -> Optional[dict]:
        try:
            data = json.loads(raw_message)
            header = data.get("header", {})
            payload = data.get("payload", {})
            
            # 1. 만약 로봇 리스트 형태의 패킷이 들어왔다면?
            if "robot_list" in payload:
                pinia_robots = []
                for idx, r in enumerate(payload["robot_list"]):
                    # Pinia의 RobotItem 인터페이스 구조에 정확히 매핑
                    pinia_robots.append({
                        "id": r.get("robot_id"),
                        "robot_ip": r.get("robot_ip"),
                        "robot_port": r.get("port"),
                        "telemetry": {
                            "status": "IDLE", # 초기 기본값 세팅 (나중에 텔레메트리로 갱신)
                            "battery": random.randint(0, 100), # 임시 랜덤 배터리 값 (실제 텔레메트리로 갱신 예정)
                            "currentMap": "Floor_1",
                            "uptime": "0h"
                        },
                        "isMain": True if idx == 0 else False, # 첫 번째 로봇을 메인 기본값으로
                        "imageUrl": "" # 초기 이미지 공백
                    })

                parsed_data = {
                    "source": source_name,
                    "timestamp": header.get("timestamp") or int(time.time() * 1000),
                    "msg_id": header.get("messageid") or str(uuid.uuid4()),
                    "target_channel": "telemetry", # 텔레메트리 채널로 분류
                    "payload": {
                        "type": "ROBOT_LIST_UPDATE", # 프론트엔드가 구별할 수 있는 서브 타입 추가
                        "robots": pinia_robots
                    }
                }

                print(f"[MessageParser] 로봇 리스트 패킷 감지 및 파싱 완료: {len(pinia_robots)} 대")  # 디버깅용 로그
                return parsed_data
            
            elif "robot_states" in payload:
                pinia_robot_states = []
                for r in payload["robot_states"]:
                    pinia_robot_states.append({
                        "id": r.get("robot_id"),
                        "telemetry": {
                            "status": r.get("status", "UNKNOWN"),
                            "battery": r.get("battery"),
                            "currentMap": r.get("current_map"),
                            "uptime": r.get("uptime"),
                        }
                    })

                parsed_data = {
                    "source": source_name,
                    "timestamp": header.get("timestamp") or int(time.time() * 1000),
                    "msg_id": header.get("messageid") or str(uuid.uuid4()),
                    "target_channel": "telemetry",
                    "payload": {
                        "type": "ROBOT_STATE_UPDATE",
                        "robot_states": pinia_robot_states
                    }
                }

                print(f"[MessageParser] 로봇 상태 패킷 감지 및 파싱 완료: {len(pinia_robot_states)} 대")  # 디버깅용 로그
                return parsed_data
            
            elif "robot_events" in payload:
                pinia_robot_events = []
                for e in payload["robot_events"]:
                    pinia_robot_events.append({
                        "event_id": e.get("event_id"),
                        "robot_id": e.get("robot_id"),
                        "type": e.get("type"),
                        "time": e.get("time"),
                        "message": e.get("message")
                    })

                parsed_data = {
                    "source": source_name,
                    "timestamp": header.get("timestamp") or int(time.time() * 1000),
                    "msg_id": header.get("messageid") or str(uuid.uuid4()),
                    "target_channel": "events", # 이벤트 채널로 분류
                    "payload": {
                        "type": "ROBOT_EVENT_UPDATE",
                        "robot_events": pinia_robot_events
                    }
                }

                print(f"[MessageParser] 로봇 이벤트 패킷 감지 및 파싱 완료: {len(pinia_robot_events)} 건")  # 디버깅용 로그
                return parsed_data
            
        except Exception as e:
            logger.error(f"[{source_name}] 파싱/라우팅 예외 발생: {e}")
            return None


# =====================================================================
# [PART 2] 업스트림 클라이언트 관리 파트 (Upstream Manager)
# =====================================================================
class UpstreamConnection:
    """여러 대의 순찰 로봇/허브(Upstream)와의 각각의 웹소켓 연결 및 무한 재시도를 전담"""

    def __init__(self, uri: str, name: str, handshake: Optional[dict] = None, on_message_cb = None, hub_info: Optional[dict] = None, manager_ref = None):
        self.uri = uri
        self.name = name
        self.handshake = handshake
        self.on_message_cb = on_message_cb
        self.hub_info = hub_info
        self.manager_ref = manager_ref
        self._running = False
        self._ws = None
        # 재시도 관련 설정 (초 단위 간격, 최대 시도 횟수)
        self.retry_interval = 5
        self.max_retries: Optional[int] = 10
    async def connect_loop(self):
        self._running = True
        attempt = 0
        while self._running:
            try:
                logger.info(f"[{self.name}] 로봇 연결 시도 ➡️ {self.uri}")
                async with websockets.connect(self.uri) as ws:
                    self._ws = ws
                    logger.info(f"[{self.name}] 로봇 연결 성공 ✅")
                    
                    if self.handshake:
                        await self._send_handshake()

                    # [기능 반영] 허브 정보가 있고 매니저 참조가 있다면 최종 연결 성공 메시지를 UI에 전송
                    if self.hub_info and self.manager_ref:
                        # 중복 관리 리스트 업데이트
                        if self not in self.manager_ref.upstreams:
                            self.manager_ref.upstreams.append(self)
                        
                        # 오직 연결에 완전히 성공한 순간에만 UI로 든든하게 성공 이벤트 발행
                        success_msg = {
                            'source': 'broadcast_manager',
                            'payload': {
                                'type': 'HUB_CONNECTED',
                                'hub': self.hub_info
                            }
                        }
                        await self.manager_ref.control_broker.broadcast(success_msg)

                    # 원본 데이터 수신 파이프라인 작동
                    async for raw_msg in ws:
                        if self.on_message_cb:
                            await self.on_message_cb(self.name, raw_msg)
                    # 연결 성공 시 재시도 카운터 초기화
                    attempt = 0
            except (websockets.ConnectionClosed, OSError) as e:
                logger.warning(f"[{self.name}] 로봇 연결 끊김 혹은 실패: {e}")
                attempt += 1
            except Exception as e:
                logger.error(f"[{self.name}] 업스트림 예외 에러: {e}")
                attempt += 1
                
            if not self._running:
                break

            # 최대 재시도 횟수 검사
            if self.max_retries is not None and attempt >= self.max_retries:
                logger.info(f"[{self.name}] 최대 재시도 {self.max_retries}회에 도달하여 연결 시도를 중단합니다.")
                break

            interval = getattr(self, 'retry_interval', 3)
            logger.info(f"[{self.name}] {interval}초 후 재연결 시도... (시도 {attempt}/{self.max_retries or '∞'})")
            await asyncio.sleep(interval)

    async def _send_handshake(self):
        try:
            h = json.loads(json.dumps(self.handshake))
            hdr = h.setdefault('header', {})
            hdr.setdefault('messageid', str(uuid.uuid4()))
            hdr.setdefault('timestamp', int(time.time() * 1000))
            await self._ws.send(json.dumps(h, ensure_ascii=False))
            logger.info(f"[{self.name}] 핸드셰이크 송신 완료")
        except Exception as e:
            logger.error(f"[{self.name}] 핸드셰이크 송신 실패: {e}")

    def stop(self):
        self._running = False


# =====================================================================
# [PART 3] 다운스트림 채널별 브로커 파트 (Downstream Channels)
# =====================================================================
class DownstreamChannelBroker:
    """독립된 전역 채널을 관리 (Telemetry, Event, Control 채널용 각각 생성됨)"""

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"[{self.channel_name}] 웹 클라이언트 접속 완료 (현재 접속자: {len(self.active_connections)}명)")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"[{self.channel_name}] 웹 클라이언트 접속 종료 (현재 접속자: {len(self.active_connections)}명)")

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
# [SYSTEM INTEGRATION] 전역 제어 아키텍처 (Orchestrator)
# =====================================================================
class BroadcastManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.upstream_tasks: List[asyncio.Task] = []
        self.upstreams: List[UpstreamConnection] = []
        
        # 목적에 맞춰 채널 브로커 세분화 (UI 단일 제어용 Control 채널 추가)
        self.telemetry_broker = DownstreamChannelBroker(channel_name="Telemetry")
        self.events_broker = DownstreamChannelBroker(channel_name="Events")
        self.control_broker = DownstreamChannelBroker(channel_name="Control")
        # 저장된 설정 항목을 보관하되 자동 연결은 수행하지 않음
        self.saved_server_entries: List[dict] = []

    def load_config(self) -> list:
        p = Path(self.config_path)
        if not p.exists():
            logger.error(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
            return []
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            logger.error(f"설정 파일 로딩 실패: {e}")
            return []

    async def pipeline_process(self, source_name: str, raw_msg: str):
        """로봇이 보낸 패킷을 분석하여 올바른 Vue 클라이언트 채널로 배송하는 파이프라인"""
        print(f"[{source_name}] 수신된 원시 메시지: {raw_msg}")  # 디버깅용 로그
        
        # 1. 가공 및 라우팅 목적지 판별
        parsed = MessageParser.parse_and_route(source_name, raw_msg)
        if not parsed:
            return

        target = parsed.pop("target_channel", "telemetry")

        # 2. 지정된 채널 브로커로 분기 전송
        if target == "events":
            await self.events_broker.broadcast(parsed)
        else:
            await self.telemetry_broker.broadcast(parsed)

    async def start(self):
        """서버 기동 시 설정 파일은 로드하지만 자동 연결은 하지 않습니다.
        웹 UI에서 `connect-hub` 요청이 들어올 때만 해당 허브로 연결을 시도합니다."""
        self.saved_server_entries = self.load_config()
        logger.info(f"설정 파일에서 {len(self.saved_server_entries)}개 항목을 로드했습니다. 자동 연결은 비활성화되었습니다.")

    async def stop(self):
        for conn in self.upstreams:
            conn.stop()
        for task in self.upstream_tasks:
            task.cancel()
        await asyncio.gather(*self.upstream_tasks, return_exceptions=True)


# =====================================================================
# FastAPI App 구동 인터페이스
# =====================================================================
app = FastAPI(title="Patrol Robot Downstream Broker System")

# CORS 미들웨어 적용
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


# ─────────────────────────────────────────────────────────────────────
# [채널 1] 로봇 텔레메트리 전용 엔드포인트 URL
# ─────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────
# [채널 2] 로봇 비상/알림 이벤트 전용 엔드포인트 URL
# ─────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────
# [채널 3] 추가 반영: UI 전용 제어 및 허브 동적 추가 엔드포인트 URL
# ─────────────────────────────────────────────────────────────────────
@app.websocket("/ws/control")
async def control_endpoint(websocket: WebSocket):
    await manager.control_broker.connect(websocket)
    # 연결된 시점에 현재 관리 중인 허브 목록을 클라이언트에 전송하여
    # 프론트엔드가 새로고침 후에도 기존 허브를 복원할 수 있도록 지원
    try:
        current_hubs = []
        for u in manager.upstreams:
            hub = getattr(u, 'hub_info', None)
            # 연결이 실제로 수립된 업스트림만 포함
            ws_obj = getattr(u, '_ws', None)
            if hub and ws_obj is not None:
                current_hubs.append(hub)

        if current_hubs:
            init_msg = {
                'source': 'broadcast_manager',
                'payload': {
                    'type': 'CURRENT_HUBS',
                    'hubs': current_hubs
                }
            }
            await websocket.send_text(json.dumps(init_msg, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Control 초기 허브 목록 전송 실패: {e}")
    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            # [핵심 로직] UI 단일 허브 추가 요청 핸들링
            if data.get('type') == 'connect-hub':
                ip = data.get('ip')
                port = data.get('port')
                
                if not ip or not port:
                    logger.warning("IP 또는 Port 누락으로 허브 추가 요청 무시")
                    continue

                # 이미 목록에 있어 돌고 있거나 완벽히 연결된 상태면 중복 생성 차단
                if any(u.uri == f"ws://{ip}:{port}/" for u in manager.upstreams):
                    logger.info(f"이미 등록되어 백그라운드 구동 중인 허브: {ip}:{port}")
                    continue

                logger.info(f"새로운 허브 동적 추가 요청 접수 -> {ip}:{port}. 즉시 백그라운드 태스크 기동.")

                # 생성 즉시 백그라운드 비동기 루프로 밀어넣기 (여기서 5초 대기하지 않고 즉시 루프 유지)
                conn = UpstreamConnection(
                    uri=f"ws://{ip}:{port}/",
                    name=f"hub_{ip}_{port}",
                    handshake=data.get('handshake'),
                    on_message_cb=manager.pipeline_process,
                    hub_info={'ip': ip, 'port': port},
                    manager_ref=manager
                )
                
                task = asyncio.create_task(conn.connect_loop())
                manager.upstream_tasks.append(task)
                
    except WebSocketDisconnect:
        manager.control_broker.disconnect(websocket)
    except Exception as e:
        logger.error(f"Control 채널 통신 예외 에러: {e}")
        manager.control_broker.disconnect(websocket)


if __name__ == '__main__':
    # 서버 가동 (포트 8000번)
    uvicorn.run(app, host="0.0.0.0", port=8000)