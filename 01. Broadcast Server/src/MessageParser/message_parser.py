import json
import time
import random
import uuid
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("MessageParser")

# 메시지 별 API 채널 및 타입 정의를 하나의 메타데이터 구조로 관리
# 개별 파서 함수들을 static메서드로 클래스 내부에 포함하기 위해, 메타데이터 구조는 아래 클래스 메서드 이후에 바인딩하거나 클래스 내부에 정의합니다.

class MessageParser:
    """수신된 데이터의 파싱 및 도메인(채널) 분류를 담당 (순수 기능 분리)"""
    
    # --- 각 패킷 유형별 전용 서브 파서 (Static Methods) ---
    @staticmethod
    def _parse_robot_list(header: dict, payload: dict) -> dict:
        return {
            "type": "ROBOT_LIST_UPDATE",
            "robots": [
                {
                    "id": r.get("robot_id"),
                    "robot_ip": r.get("robot_ip"),
                    "robot_port": r.get("port"),
                }
                for r in payload.get("robot_list", [])
            ]
        }

    @staticmethod
    def _parse_robot_states(header: dict, payload: dict) -> dict:
        return {
            "type": "ROBOT_STATE_UPDATE",
            "robot_states": [
                {
                    "id": r.get("robot_id"),
                    "telemetry": {
                        "status": r.get("status", "UNKNOWN"),
                        "battery": r.get("battery"),
                        "currentMap": r.get("current_map"),
                        "uptime": r.get("uptime"),
                    }
                }
                for r in payload.get("robot_states", [])
            ]
        }

    @staticmethod
    def _parse_robot_events(header: dict, payload: dict) -> dict:
        return {
            "type": "ROBOT_EVENT_UPDATE",
            "robot_events": [
                {
                    "event_id": e.get("event_id"),
                    "robot_id": e.get("robot_id"),
                    "type": e.get("type"),
                    "time": e.get("time"),
                    "message": e.get("message")
                }
                for e in payload.get("robot_events", [])
            ]
        }

    @staticmethod
    def _parse_va_meta(header: dict, payload: dict) -> dict:
        event_status = "UNKNOWN"
        if payload.get("event_status") == 1:
            event_status = "DETECTED"
        elif payload.get("event_status") == 4:
            event_status = "FINISHED"

        return {
            "type": "ROBOT_EVENT_UPDATE",
            "robot_events": [
                {
                    "event_id": f"{payload.get('uid')}_{payload.get('type')}_{payload.get('event_status')}_{random.randint(100000, 999999)}",  # vaMeta는 고유 이벤트 ID가 없으므로 임의 생성),
                    "robot_id": "NEO-01",
                    "type": "SYSTEM",
                    "time": datetime.fromtimestamp(header.get("timestamp") / 1000).strftime("%H:%M:%S"),
                    "message": f"({event_status}) {payload.get('vlm_description')}"
                }
            ]
        }

    # --- 파서 및 채널 매핑 테이블 테이블 ---
    # 신규 메시지가 추가되면 이 딕셔너리에 '키', '채널', '파서함수'만 등록하면 됩니다.
    PARSER_REGISTRY = {
        "robot_list_update": {"channel": "telemetry", "parser": _parse_robot_list.__func__},
        "robot_state_update": {"channel": "telemetry", "parser": _parse_robot_states.__func__},
        "robot_event_update": {"channel": "events", "parser": _parse_robot_events.__func__},
        "event_detected": {"channel": "events", "parser": _parse_va_meta.__func__},
        "event_finished": {"channel": "events", "parser": _parse_va_meta.__func__},
    }

    @staticmethod
    def parse_and_route(source_name: str, raw_message: str) -> Optional[dict]:
        try:
            data = json.loads(raw_message)
            print(f"Received raw message from {source_name}: {data}")

            header = data.get("header", {})
            payload = data.get("payload", {}) or {}

            # 1. payload에 존재하는 key를 기반으로 등록된 매핑 정보 찾기
            matched_key = None
            print(header.get("type", ""))
            for key in MessageParser.PARSER_REGISTRY:
                if key in header.get("type", ""):
                    matched_key = key
                    break

            if not matched_key:
                logger.warning(f"[{source_name}] 지원하지 않거나 비어있는 패킷 형태입니다. ")
                return None

            registry_info = MessageParser.PARSER_REGISTRY[matched_key]

            # 2. 공통 헤더 구성 및 타겟 채널 자동 분류
            parsed_message = {
                "source": source_name,
                "timestamp": header.get("timestamp") or int(time.time() * 1000),
                "msg_id": header.get("messageid") or str(uuid.uuid4()),
                "target_channel": registry_info["channel"]
            }

            # 3. 매핑된 전용 파서 함수를 호출하여 header와 payload를 함께 전달
            parser_func = registry_info["parser"]
            parsed_message["payload"] = parser_func(header, payload)

            return parsed_message
            
        except Exception as e:
            logger.error(f"[{source_name}] 파싱 예외 발생: {e}")
            return None