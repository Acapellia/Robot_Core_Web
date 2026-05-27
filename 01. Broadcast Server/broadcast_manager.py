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
# [PART 1] 데이터 파싱 클래스 (Parser) - 오직 변환만 담당
# =====================================================================
from src.MessageParser.message_parser import MessageParser


# =====================================================================
# [PART 2] 웹소켓 연결 및 수신 태스크 (Upstream Manager)
# =====================================================================
class UpstreamConnection:
    """오직 개별 웹소켓의 연결 유지와 원시 메시지 수신(Ingest)만 담당"""

    def __init__(self, uri: str, name: str, handshake: Optional[dict] = None, inbound_queue: Optional[asyncio.Queue] = None, hub_info: Optional[dict] = None, manager_ref = None):
        self.uri = uri
        self.name = name
        self.handshake = handshake
        self.inbound_queue = inbound_queue  # 중앙에서 주입받는 큐
        self.hub_info = hub_info
        self.manager_ref = manager_ref
        self._running = False
        self._ws = None
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

                    if self.hub_info and self.manager_ref:
                        if self not in self.manager_ref.upstreams:
                            self.manager_ref.upstreams.append(self)
                        
                        success_msg = {
                            'source': 'broadcast_manager',
                            'payload': {
                                'type': 'HUB_CONNECTED',
                                'hub': self.hub_info
                            }
                        }
                        # 내부 제어 채널로 알림
                        await self.manager_ref.control_broker.broadcast(success_msg)

                    attempt = 0
                    # [수정] 수신된 원시 메시지를 처리하지 않고 즉시 큐(Queue)로 던짐
                    async for raw_msg in ws:
                        if self.inbound_queue:
                            await self.inbound_queue.put((self.name, raw_msg))
                            
            except (websockets.ConnectionClosed, OSError) as e:
                logger.warning(f"[{self.name}] 로봇 연결 끊김 혹은 실패: {e}")
                attempt += 1
            except Exception as e:
                logger.error(f"[{self.name}] 업스트림 예외 에러: {e}")
                attempt += 1
                
            if not self._running:
                break

            if self.max_retries is not None and attempt >= self.max_retries:
                logger.info(f"[{self.name}] 최대 재시도 {self.max_retries}회에 도달하여 중단합니다.")
                break

            await asyncio.sleep(self.retry_interval)

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
# [PART 3] 다운스트림 채널 브로커 (Downstream Channels)
# =====================================================================
class DownstreamChannelBroker:
    """오직 들어온 완제품 메시지를 클라이언트에게 전송(방송)하는 역할만 전담"""

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
# [SYSTEM INTEGRATION] 메시지 수집/분배/중계 아키텍처 (Orchestrator)
# =====================================================================
class BroadcastManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.upstream_tasks: List[asyncio.Task] = []
        self.upstreams: List[UpstreamConnection] = []
        
        # 1. 채널 브로커 세분화
        self.telemetry_broker = DownstreamChannelBroker(channel_name="Telemetry")
        self.events_broker = DownstreamChannelBroker(channel_name="Events")
        self.control_broker = DownstreamChannelBroker(channel_name="Control")
        
        self.saved_server_entries: List[dict] = []

        # ⭐️ [핵심 개선] 질문자님의 아키텍처 철학 반영: 두 개의 독립적인 메시지 큐 생성
        self.raw_message_queue = asyncio.Queue()     # 수신된 원시 메시지가 모이는 큐
        self.parsed_message_queue = asyncio.Queue()  # 파싱이 완료된 메시지가 모이는 큐

        # 백그라운드 전용 일꾼(Worker)들을 담을 리스트
        self.worker_tasks: List[asyncio.Task] = []

    def load_config(self) -> list:
        p = Path(self.config_path)
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            logger.error(f"설정 파일 로딩 실패: {e}")
            return []

    # -----------------------------------------------------------------
    # 🏃‍♂️ 백그라운드 독립 일꾼 1: 오직 파싱만 전담 (Parser Worker)
    # -----------------------------------------------------------------
    async def _message_parser_worker(self):
        """raw_message_queue를 상시 감시하며 데이터가 들어오면 파싱 후 다음 단계 큐로 넘김"""
        logger.info("[Parser Worker] 가동 시작 - 원시 메시지 파싱 전담")
        while True:
            try:
                source_name, raw_msg = await self.raw_message_queue.get()
                
                # 오직 파싱 및 목적지 판별만 수행 (기능적 완벽 분리)
                parsed = MessageParser.parse_and_route(source_name, raw_msg)
                print(f"Parsed message from {source_name}: {parsed}")
                
                if parsed:
                    # 파싱이 끝난 결과물을 분배(Delivery) 큐로 토스
                    await self.parsed_message_queue.put(parsed)
                    
                self.raw_message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Parser Worker] 에러 발생: {e}")

    # -----------------------------------------------------------------
    # 🏃‍♂️ 백그라운드 독립 일꾼 2: 오직 재전송/분배만 전담 (Delivery Worker)
    # -----------------------------------------------------------------
    async def _message_delivery_worker(self):
        """parsed_message_queue를 상시 감시하며 가공된 메시지를 최종 목적지 채널로 전송"""
        logger.info("[Delivery Worker] 가동 시작 - 파싱된 메시지 목적지 배송 전담")
        while True:
            try:
                parsed_msg = await self.parsed_message_queue.get()
                
                # 목적지 타겟 채널 추출
                target = parsed_msg.pop("target_channel", "telemetry")

                # 알맞은 목적지 브로커를 찾아서 실시간 방송(Broadcast)
                if target == "events":
                    await self.events_broker.broadcast(parsed_msg)
                else:
                    await self.telemetry_broker.broadcast(parsed_msg)
                    
                self.parsed_message_queue.task_done()
            except asyncio.read_to_end_of_file:
                break
            except Exception as e:
                logger.error(f"[Delivery Worker] 에러 발생: {e}")

    async def start(self):
        """서버 기동 시 백그라운드 전용 파이프라인 일꾼들을 먼저 깨웁니다."""
        self.saved_server_entries = self.load_config()
        
        # 역할별 전용 일꾼(태스크) 배치 및 구동
        self.worker_tasks.append(asyncio.create_task(self._message_parser_worker()))
        self.worker_tasks.append(asyncio.create_task(self._message_delivery_worker()))
        
        logger.info(f"설정 로드 완료 및 역할별 파이프라인 일꾼 워커(Parser/Delivery) 가동 완료.")

    async def stop(self):
        # 웹소켓 업스트림 중단
        for conn in self.upstreams:
            conn.stop()
        for task in self.upstream_tasks:
            task.cancel()
            
        # 내부 파이프라인 일꾼 워커 중단
        for task in self.worker_tasks:
            task.cancel()
            
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
    try:
        current_hubs = []
        for u in manager.upstreams:
            hub = getattr(u, 'hub_info', None)
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

            if data.get('type') == 'connect-hub':
                ip = data.get('ip')
                port = data.get('port')
                
                if not ip or not port:
                    continue

                if any(u.uri == f"ws://{ip}:{port}/" for u in manager.upstreams):
                    continue

                logger.info(f"새로운 허브 동적 추가 요청 접수 -> {ip}:{port}")

                # [수정] 수신된 원시 데이터를 쌓아둘 'manager.raw_message_queue'를 인자로 주입합니다.
                conn = UpstreamConnection(
                    uri=f"ws://{ip}:{port}/",
                    name=f"hub_{ip}_{port}",
                    handshake=data.get('handshake'),
                    inbound_queue=manager.raw_message_queue,
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
    uvicorn.run(app, host="0.0.0.0", port=8000)