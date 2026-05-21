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
import uvicorn

# 시스템 표준 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BroadcastSystem")


# =====================================================================
# [PART 1] 데이터 분류 및 파싱 파트 (Message Router & Parser)
# =====================================================================
# broadcast_manager.py 내의 MessageParser 클래스 수정
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

                print(f"[MessageParser] 로봇 리스트 패킷 감지 및 파싱 완료: {len(pinia_robots)} 대, parsed_data: {parsed_data}")  # 디버깅용 로그
                
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

                print(f"[MessageParser] 로봇 상태 패킷 감지 및 파싱 완료: {len(pinia_robot_states)} 대, parsed_data: {parsed_data}")  # 디버깅용 로그

                return parsed_data
            
        except Exception as e:
            logger.error(f"[{source_name}] 파싱/라우팅 예외 발생: {e}")
            return None


# =====================================================================
# [PART 2] 업스트림 클라이언트 관리 파트 (Upstream Manager)
# =====================================================================
class UpstreamConnection:
    """여러 대의 순찰 로봇(Upstream)과의 각각의 웹소켓 연결을 전담"""

    def __init__(self, uri: str, name: str, handshake: Optional[dict] = None, on_message_cb = None):
        self.uri = uri
        self.name = name
        self.handshake = handshake
        self.on_message_cb = on_message_cb
        self._running = False
        self._ws = None

    async def connect_loop(self):
        self._running = True
        while self._running:
            try:
                logger.info(f"[{self.name}] 로봇 연결 시도 ➡️ {self.uri}")
                async with websockets.connect(self.uri) as ws:
                    self._ws = ws
                    logger.info(f"[{self.name}] 로봇 연결 성공 ✅")
                    
                    if self.handshake:
                        await self._send_handshake()

                    async for raw_msg in ws:
                        if self.on_message_cb:
                            await self.on_message_cb(self.name, raw_msg)
                            
            except (websockets.ConnectionClosed, OSError) as e:
                logger.warning(f"[{self.name}] 로봇 연결 끊김: {e}")
            except Exception as e:
                logger.error(f"[{self.name}] 업스트림 예외 에러: {e}")
                
            if self._running:
                logger.info(f"[{self.name}] 3초 후 재연결 시도...")
                await asyncio.sleep(3)

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
    """독립된 전역 채널을 관리 (Telemetry 채널용, Event 채널용 각각 생성됨)"""

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"[{self.channel_name}] 웹 클라이언트 접속 완료 (현재 접속자: {len(self.active_connections)}명)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"[{self.channel_name}] 웹 클라이언트 접속 종료 (현재 접속자: {len(self.active_connections)}명)")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected_clients = set()
        
        for connection in self.active_connections:
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
        
        # [현업의 포인트] 목적에 맞춰 채널 브로커를 분리하여 인스턴스화합니다.
        self.telemetry_broker = DownstreamChannelBroker(channel_name="Telemetry")
        self.events_broker = DownstreamChannelBroker(channel_name="Events")

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
        server_entries = self.load_config()
        for entry in server_entries:
            ip = entry.get('ip')
            port = entry.get('port')
            if not ip or not port:
                continue
            
            name = entry.get('type') or entry.get('name') or 'unknown_robot'
            scheme = entry.get('scheme', 'ws')
            path = entry.get('path', '/')
            uri = f"{scheme}://{ip}:{port}{path}"
            
            conn = UpstreamConnection(
                uri=uri, 
                name=name, 
                handshake=entry.get('handshake'),
                on_message_cb=self.pipeline_process # 파이프라인 메서드를 콜백으로 연결
            )
            self.upstreams.append(conn)
            self.upstream_tasks.append(asyncio.create_task(conn.connect_loop()))

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
            # 커넥션 유지 및 끊김 감지를 위한 빈 수신 루프
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


if __name__ == '__main__':
    # 서버 가동 (포트 8000번)
    uvicorn.run(app, host="0.0.0.0", port=8000)