import json
import websockets
import asyncio
from .base import BaseConnection
from typing import Optional


class PureWebSocketConnection(BaseConnection):
    """인증 단계 없이 바로 WebSocket에 접속하는 간단한 연결 클래스.

    사용 사례: 외부 인증이 필요없는 순수 WebSocket 엔드포인트에 연결할 때 사용합니다.
    옵션으로 최초 핸드셰이크용 페이로드를 전송할 수 있습니다.
    """

    def __init__(self, ws_uri: str, handshake_payload: Optional[dict] = None, **kwargs):
        super().__init__(**kwargs)
        self.ws_uri = ws_uri
        self.handshake_payload = handshake_payload

    async def _establish_websocket(self) -> websockets.WebSocketClientProtocol:
        """WebSocket 접속 + 핸드셰이크 전송 + ACK 응답 검증"""
        ws = await websockets.connect(self.ws_uri, subprotocols=["hub-protocol"], max_size=None)
        if self.handshake_payload:
            # 1. 핸드셰이크 페이로드 전송
            handshake_msg = json.dumps(self.handshake_payload, ensure_ascii=False)
            print(handshake_msg)
            await ws.send(handshake_msg)
            
            # 2. 서버로부터 ACK 응답 대기 (비동기 대기)
            # 10초 동안 응답이 없으면 타임아웃 발생
            try:
                ack_response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                ack_data = json.loads(ack_response)
                
                # 3. ACK 검증 (로봇 서버가 'accepted'를 보내는지 확인)
                payload = ack_data.get("payload", {})
                if payload.get("status") != "accepted":
                    await ws.close()
                    raise Exception(f"Handshake Rejected: {ack_response}")
                    
            except asyncio.TimeoutError:
                await ws.close()
                raise Exception("Handshake Timeout: No ACK received from robot")
                
        return ws