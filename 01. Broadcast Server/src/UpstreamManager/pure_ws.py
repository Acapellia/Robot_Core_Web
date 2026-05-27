import json
import websockets
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
        """WebSocket에 접속하고(연결 성공 시) 필요하면 초기 핸드셰이크 페이로드를 전송합니다."""
        ws = await websockets.connect(self.ws_uri)
        if self.handshake_payload:
            await ws.send(json.dumps(self.handshake_payload, ensure_ascii=False))
        return ws
