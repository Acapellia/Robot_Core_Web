import json
import logging
from functools import partial
from typing import Optional
from urllib.parse import quote_plus
from fastapi import WebSocket

from .pure_ws import PureWebSocketConnection
from .http_auth_ws import HttpAuthWebSocketConnection

logger = logging.getLogger("UpstreamManager.ConnectionManager")


def register_upstream(conn_obj, manager) -> None:
    """중앙화된 업스트림 등록 로직: 중복 제거 및 manager.upstreams에 추가"""
    if conn_obj in manager.upstreams:
        return
    manager.upstreams.append(conn_obj)


def unregister_upstream(conn_obj, manager) -> None:
    """업스트림 제거 로직: 존재하면 제거"""
    try:
        if conn_obj in manager.upstreams:
            manager.upstreams.remove(conn_obj)
    except Exception:
        logger.exception("upstream 제거 중 예외 발생")


async def _notify_connect(conn_obj, manager, kind: str, ip: str, port: int):
    conn_obj.hub_info = {"ip": ip, "port": port, "uri": f"ws://{ip}:{port}/"}
    register_upstream(conn_obj, manager)

    payload_key = "hub" if kind == "HUB" else "va"
    msg_type = "HUB_CONNECTED" if kind == "HUB" else "VA_CONNECTED"

    success_msg = {
        "source": "broadcast_manager",
        "payload": {
            "type": msg_type,
            payload_key: conn_obj.hub_info,
        },
    }
    await manager.control_broker.broadcast(success_msg)


def _gather_connected_by_prefix(manager, prefix: str):
    results = []
    for u in manager.upstreams:
        name = getattr(u, "name", "") or ""
        if not name.startswith(prefix):
            continue
        hub = getattr(u, "hub_info", None)
        ws_obj = getattr(u, "_ws", None)
        if hub and ws_obj is not None:
            results.append(hub)
    return results


async def send_connected_hubs_to_web(websocket: WebSocket, manager) -> None:
    # backwards-compatible wrapper: hubs use 'hubs' key and CURRENT_HUBS type
    try:
        hubs = _gather_connected_by_prefix(manager, "hub_")
        if hubs:
            init_msg = {
                "source": "broadcast_manager",
                "payload": {"type": "CURRENT_HUBS", "hubs": hubs},
            }
            await websocket.send_text(json.dumps(init_msg, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Control 초기 허브 목록 전송 실패: {e}")


async def send_connected_vas_to_web(websocket: WebSocket, manager) -> None:
    # VA-specific wrapper: uses 'vas' key and CURRENT_VAS type
    try:
        vas = _gather_connected_by_prefix(manager, "va_")
        if vas:
            init_msg = {
                "source": "broadcast_manager",
                "payload": {"type": "CURRENT_VAS", "vas": vas},
            }
            await websocket.send_text(json.dumps(init_msg, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Control 초기 VA 목록 전송 실패: {e}")


def build_hub_connection(data: dict, manager) -> Optional[PureWebSocketConnection]:
    ip = data.get("ip")
    port = data.get("port")
    if not ip or not port:
        return None

    name = f"hub_{ip}_{port}"
    if any(getattr(u, "name", None) == name for u in manager.upstreams):
        return None

    on_connect = partial(_notify_connect, manager=manager, kind="HUB", ip=ip, port=port)

    conn = PureWebSocketConnection(
        ws_uri=f"ws://{ip}:{port}/",
        handshake_payload=data.get("handshake"), #[HUB] 실제 허브는 해당 내용 필요
        name=name,
        inbound_queue=manager.raw_message_queue,
        outbound_queue=None,
        retry_interval=data.get("retry_interval", 5),
        max_retries=data.get("max_retries", 10),
        on_connect=on_connect,
    )

    return conn


def build_va_connection(data: dict, manager) -> Optional[HttpAuthWebSocketConnection]:
    ip = data.get("ip")
    port = data.get("port")
    id_val = data.get("id")
    pw_val = data.get("pw")
    login_path = data.get("handshake")

    if not ip or not port:
        return None

    name = f"va_{ip}_{port}"
    if any(getattr(u, "name", None) == name for u in manager.upstreams):
        return None

    on_connect = partial(_notify_connect, manager=manager, kind="VA", ip=ip, port=port)

    auth_url = f"http://{ip}:{port}{login_path}"
        
    login_payload = {"id": id_val, "pw": pw_val, "keepAliveTimeOut": 900}

    ws_template = data.get("ws_uri_template") or f"ws://{ip}:{port}/?api-key={{token}}&ch=0,1,2,3&hubMeta"

    def ws_factory(token, template=ws_template):
        parts = [f"api-key={quote_plus(str(token))}", "ch=0,1,2,3", "hubMeta"]
        query = "&".join(parts)
        if "{token}" in template:
            return template.replace("{token}", quote_plus(str(token)))
        return f"ws://{ip}:{port}/?{query}"

    conn = HttpAuthWebSocketConnection(
        auth_url=auth_url,
        ws_uri_factory=ws_factory,
        login_payload=login_payload,
        name=name,
        inbound_queue=manager.raw_message_queue,
        outbound_queue=None,
        subprotocols=data.get("subprotocols", ["va-metadata"]),
        retry_interval=data.get("retry_interval", 5),
        max_retries=data.get("max_retries", 10),
        on_connect=on_connect,
        on_auth_token=data.get("on_auth_token"),
    )

    return conn
