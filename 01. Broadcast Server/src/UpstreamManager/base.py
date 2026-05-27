import asyncio
import json
import logging
from typing import Optional, Any, Callable, Awaitable
import aiohttp
import websockets

logger = logging.getLogger(__name__)


class BaseConnection:
    def __init__(
        self,
        name: str,
        inbound_queue: Optional[asyncio.Queue] = None,
        outbound_queue: Optional[asyncio.Queue] = None,
        retry_interval: int = 5,
        max_retries: Optional[int] = 10,
        on_connect: Optional[Callable[[Any], Awaitable[None]]] = None,
    ):
        self.name = name
        self.inbound_queue = inbound_queue
        self.outbound_queue = outbound_queue
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.on_connect = on_connect

        self._running = False
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._send_task: Optional[asyncio.Task] = None

    async def _establish_websocket(self) -> websockets.WebSocketClientProtocol:
        raise NotImplementedError

    async def run_loop(self):
        self._running = True
        attempt = 0

        while self._running:
            try:
                logger.info(f"[{self.name}] 연결 시도 중... (시도: {attempt + 1})")
                self._ws = await self._establish_websocket()
                logger.info(f"[{self.name}] WebSocket 연결 성공")

                attempt = 0

                if self.on_connect:
                    try:
                        await self.on_connect(self)
                    except Exception:
                        logger.exception("on_connect callback 실패")

                if self.outbound_queue:
                    self._send_task = asyncio.create_task(self._send_loop())

                async for raw_msg in self._ws:
                    if self.inbound_queue:
                        await self.inbound_queue.put((self.name, raw_msg))

            except (websockets.ConnectionClosed, OSError, aiohttp.ClientError) as e:
                logger.warning(f"[{self.name}] 연결 실패/끊김: {e}")
                attempt += 1
            except Exception as e:
                logger.error(f"[{self.name}] 예외 발생: {e}", exc_info=True)
                attempt += 1
            finally:
                # 연결이 끊기거나 예외가 발생한 후 실행됩니다.
                # 하위 클래스가 추가 정리(예: 인증 토큰 초기화)를 원하면
                # `_on_disconnect()`를 오버라이드하도록 허용합니다.
                try:
                    await self._on_disconnect()
                except Exception:
                    logger.exception("_on_disconnect 처리 중 예외 발생")

                await self._clear_send_task()

                # _ws 객체는 더 이상 유효하지 않으므로 명시적으로 해제
                self._ws = None

            if not self._running:
                break

            if self.max_retries is not None and attempt >= self.max_retries:
                logger.error(f"[{self.name}] 최대 재시도 도달({self.max_retries}) - 중단")
                break

            await asyncio.sleep(self.retry_interval)

    async def _send_loop(self):
        try:
            while self._running and self._ws:
                msg = await self.outbound_queue.get()
                try:
                    if isinstance(msg, dict):
                        msg = json.dumps(msg, ensure_ascii=False)
                    await self._ws.send(msg)
                    self.outbound_queue.task_done()
                except Exception as e:
                    logger.error(f"[{self.name}] 송신 에러: {e}")
                    self.outbound_queue.task_done()
                    break
        except asyncio.CancelledError:
            pass

    async def _clear_send_task(self):
        if self._send_task and not self._send_task.done():
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass
        self._send_task = None

    def stop(self):
        self._running = False
        if self._ws:
            asyncio.create_task(self._ws.close())

    async def _on_disconnect(self):
        """호출 시점: 연결이 끊기거나 예외가 발생한 직후.
        하위 클래스가 재로그인이나 토큰 초기화가 필요하면 이 메서드를 오버라이드하세요.
        기본 동작은 아무 것도 하지 않습니다.
        """
        return None
