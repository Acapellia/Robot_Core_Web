import json
import logging
import asyncio
import aiohttp
import websockets
from .base import BaseConnection
from typing import Callable, Optional, List

logger = logging.getLogger(__name__)


class HttpAuthWebSocketConnection(BaseConnection):
    def __init__(
        self,
        auth_url: str,
        ws_uri_factory: Callable[[str], str],
        login_payload: dict,
        auth_header_factory: Optional[Callable[[str], dict]] = None,
        subprotocols: Optional[List[str]] = None,
        on_auth_token: Optional[Callable[[str, object], None]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.auth_url = auth_url
        self.ws_uri_factory = ws_uri_factory
        self.login_payload = login_payload
        self.auth_header_factory = auth_header_factory
        # 원하는 WebSocket 서브프로토콜 리스트 (예: ["va-metadata"])을 저장
        self.subprotocols = subprotocols
        # Optional callback invoked when auth token is obtained.
        # Signature: on_auth_token(token: str, conn_obj: HttpAuthWebSocketConnection)
        self.on_auth_token = on_auth_token

    async def _do_login(self) -> str:
        """HTTP 로그인 수행 후 인증 토큰을 반환합니다.

        이 메서드는 `self.auth_url`에 POST 요청을 보내고 응답 JSON을 파싱하여
        토큰을 추출합니다. 지원하는 토큰 키 이름들을 확인한 뒤
        `self.auth_token`에 저장하고 토큰 문자열을 반환합니다.
        """
        # 로그인 로직을 별도 메서드로 분리하여 가독성 향상
        token = None
        async with aiohttp.ClientSession() as session:
            logger.info(f"[{self.name}] (LOGIN PHASE) {self.auth_url}에 POST 요청 중...")
            async with session.post(self.auth_url, json=self.login_payload) as response:
                status = response.status
                text = await response.text()
                if status < 200 or status >= 300:
                    raise ValueError(f"인증 요청 실패: status={status}, body={text}")

                try:
                    res_data = json.loads(text)
                except Exception:
                    raise ValueError(f"인증 응답 JSON 파싱 실패: status={status}, body={text}")

                candidates = ["token", "api_key", "api-key", "apikey", "apiKey"]
                for k in candidates:
                    if k in res_data:
                        token = res_data.get(k)
                        break

                if not token and isinstance(res_data.get("data"), dict):
                    for k in candidates:
                        if k in res_data["data"]:
                            token = res_data["data"].get(k)
                            break

                if not token:
                    raise ValueError(f"인증 응답에 토큰이 없습니다: status={status}, body={text}")

                # 로그인 성공: 인스턴스 상태에 토큰 저장
                self.auth_token = token
                logger.info(f"[{self.name}] (LOGIN PHASE) 인증 성공, 토큰 수신 완료")

                # Notify manager or caller about received token (if callback provided)
                if self.on_auth_token:
                    try:
                        maybe = self.on_auth_token(self.auth_token, self)
                        if asyncio.iscoroutine(maybe):
                            await maybe
                    except Exception:
                        logger.exception("on_auth_token callback error")
        return token

    async def _establish_websocket(self) -> websockets.WebSocketClientProtocol:
        # 로그인 프로세스를 통해 api-key 획득
        token = await self._do_login()

        # ------------------------------------------------------------
        # 단계 2: WebSocket 업그레이드 (Upgrade Phase)
        # - 로그인으로 얻은 토큰을 사용해 WS URI를 생성하고 핸드셰이크를 시도한다.
        # - 필요하면 서브프로토콜을 요청하여 서버의 해당 핸들러로 라우팅되게 한다.
        # ------------------------------------------------------------
        final_ws_uri = self.ws_uri_factory(token)
        self.ws_uri_used = final_ws_uri
        extra_headers = self.auth_header_factory(token) if self.auth_header_factory else None

        try:
            connect_kwargs = {}
            if extra_headers:
                connect_kwargs['extra_headers'] = extra_headers
            if self.subprotocols:
                connect_kwargs['subprotocols'] = self.subprotocols

            logger.info(f"[{self.name}] (UPGRADE PHASE) WebSocket 접속 시도: {final_ws_uri}, subprotocols={self.subprotocols}")
            ws = await websockets.connect(final_ws_uri, **connect_kwargs)
            # 연결 성공 시 ws 객체를 반환
            return ws
        except TypeError:
            # 일부 환경에서 extra_headers가 실패할 수 있으므로 폴백: 헤더를 쿼리 파라미터로 인코딩
            from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

            if extra_headers:
                parts = urlsplit(final_ws_uri)
                q = dict(parse_qsl(parts.query))
                q.update({k: str(v) for k, v in extra_headers.items()})
                new_query = urlencode(q)
                final_ws_uri = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

            logger.info(f"[{self.name}] (UPGRADE PHASE) 폴백으로 쿼리 파라미터 방식 사용: {final_ws_uri}")

            if self.subprotocols:
                ws = await websockets.connect(final_ws_uri, subprotocols=self.subprotocols)
            else:
                ws = await websockets.connect(final_ws_uri)
            return ws

    async def _on_disconnect(self):
        """연결이 끊기면 호출됩니다.
        - 인증 토큰을 초기화하여 다음 시도 시 다시 HTTP 로그인부터 시작하게 합니다.
        - 사용자가 원하는 동작(로그아웃 처리 등)을 이곳에 추가할 수 있습니다.
        """
        logger.info(f"[{self.name}] 연결 종료 감지 - 인증 상태 초기화 및 다음 시도에서 로그인 재시도")
        try:
            self.auth_token = None
            self.ws_uri_used = None
        except Exception:
            logger.exception("_on_disconnect 처리 중 에러")
