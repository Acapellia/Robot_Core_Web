#!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid
import time
import argparse
import os
from typing import Dict, Any
import random
import copy

CONNECTED = set()

def load_templates(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_header(tpl: Dict[str, Any], session_id: str | None = None, priority: int | None = None):
    h = tpl.get("header", {})
    # support both forms in templates: 'source' or 'protocol_source'
    src = h.get("protocol_source") or h.get("source") or h.get("Protocol_Source") or h.get("sourceSystem")
    cat = h.get("protocol_category") or h.get("category") or h.get("Protocol_Category")
    # Build header matching docx example (lowercase keys)
    return {
        "version": h.get("version", "1.0"),
        "type": h.get("type", ""),
        "messageid": str(uuid.uuid4()),
        "sessionid": session_id or h.get("SessionID") or h.get("sessionid", "0"),
        "timestamp": int(time.time() * 1000),
        "protocol_source": str(src).upper() if src is not None else "",
        "protocol_category": str(cat).upper() if cat is not None else "",
        "priority": priority if priority is not None else h.get("priority", 0)
    }

async def handler(websocket, path=None):
    peer = websocket.remote_address
    print(f"Client connected: {peer}")
    CONNECTED.add(websocket)
    try:
        async for msg in websocket:
            print(f"[Client {peer}] {msg}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED.remove(websocket)
        print(f"Client disconnected: {peer}")

async def send_message(message: Dict[str, Any]):
    if not CONNECTED:
        print("[WARN] No connected clients to send to.")
        return
    payload = json.dumps(message, ensure_ascii=False)
    websockets_snapshot = list(CONNECTED)
    for ws in websockets_snapshot:
        try:
            await ws.send(payload)
            print(f"Sent to {ws.remote_address}")
        except Exception as e:
            print(f"Send error to {ws.remote_address}: {e}")

def prompt_for_overrides(payload: Any):
    # If payload is a simple value, return possibly overridden value
    if isinstance(payload, (str, int, float, bool)):
        val = input(f"값 입력 (기본={payload}) -> ").strip()
        if val == "":
            return payload
        # try to cast
        try:
            if isinstance(payload, bool):
                return val.lower() in ("1","true","t","yes","y")
            if isinstance(payload, int):
                return int(val)
            if isinstance(payload, float):
                return float(val)
        except:
            return val
    if isinstance(payload, dict):
        result = {}
        for k, v in payload.items():
            print(f"필드: {k}")
            result[k] = prompt_for_overrides(v)
        return result
    if isinstance(payload, list):
        print("리스트 항목 편집: 기본값 출력을 편집하려면 JSON으로 입력하세요.")
        print(json.dumps(payload, ensure_ascii=False))
        val = input("리스트(또는 빈 입력으로 기본 유지) -> ").strip()
        if val == "":
            return payload
        try:
            parsed = json.loads(val)
            return parsed
        except Exception as e:
            print(f"파싱 실패: {e}")
            return payload
    return payload

async def cli_loop(templates_path: str, host: str, port: int):
    templates = load_templates(templates_path)
    help_text = """
사용법:
  번호를 입력하여 템플릿 선택
  `list` - 템플릿 목록
  `clients` - 연결된 클라이언트 수 표시
  `quit` - 종료
"""
    print(f"WebSocket sender server running on {host}:{port}")
    print(help_text)
    # 처음 시작 시 템플릿 목록을 자동으로 출력
    print("템플릿 목록:")
    for i, t in enumerate(templates):
        print(f"  [{i}] {t.get('title')} (id={t.get('id')})")
    print("  [q] quit")
    while True:
        cmd = await asyncio.to_thread(input, "선택> ")
        cmd = cmd.strip()
        if cmd == "" or cmd == "list":
            print("템플릿 목록:")
            for i, t in enumerate(templates):
                print(f"  [{i}] {t.get('title')} (id={t.get('id')})")
            print("  [q] quit")
            continue
        if cmd == "clients":
            print(f"연결된 클라이언트: {len(CONNECTED)}")
            continue
        if cmd in ("q","quit","exit"):
            print("서버를 종료합니다...")
            break
        # try parse as index
        try:
            idx = int(cmd)
            tpl = templates[idx]
        except Exception:
            print("유효한 입력이 아닙니다. 인덱스 또는 명령을 입력하세요.")
            continue

        print(f"선택된 템플릿: {tpl.get('title')}")
        # 템플릿의 header와 payload를 가져옵니다
        payload = tpl.get('payload', {})

        # robot_state 템플릿이면 각 로봇의 battery와 uptime을 랜덤으로 재설정
        if tpl.get('id') == 'robot_state' or tpl.get('type') == 'robot_state' or tpl.get('title','').lower().find('robot state') != -1:
            payload = copy.deepcopy(payload)
            robot_states = payload.get('robot_states') or payload.get('robot_states', [])
            if isinstance(robot_states, list):
                for state in robot_states:
                    # battery: 0~100
                    state['battery'] = random.randint(0, 100)
                    # uptime: 0h 00m ~ 12h 00m (if 12h then 00m)
                    h = random.randint(0, 12)
                    m = 0 if h == 12 else random.randint(0, 59)
                    state['uptime'] = f"{h}h {m:02d}m"

        header = build_header(tpl)
        message = {"header": header, "payload": payload}

        # 선택 시 기본 동작: 템플릿을 한 번만 전송
        await send_message(message)
        print("메시지 전송 시도 완료")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--templates', default=os.path.join(os.path.dirname(__file__), 'templates.json'))
    args = parser.parse_args()

    server = await websockets.serve(handler, args.host, args.port)

    try:
        await cli_loop(args.templates, args.host, args.port)
    finally:
        server.close()
        await server.wait_closed()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n종료')
