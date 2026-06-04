"""
Utilities for creating message IDs and timestamps compatible with Robot_Hub.

Provides:
- `MessageUtils.generate_uuid()` : RFC4122 UUID4 string
- `MessageUtils.current_timestamp_ms()` : integer milliseconds since epoch
- `MessageUtils.make_header(...)` : convenience to build a protocol header dict including
  `messageid`/`messageID` and `timestamp` fields (keeps both casing variants)
"""
from __future__ import annotations

import time
import uuid
from typing import Optional, Dict, Any


class MessageUtils:
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a UUID string (UUID4).

        Matches the semantics of Robot_Hub's `GenerateUuid()` used for messageID.
        """
        return str(uuid.uuid4())

    @staticmethod
    def current_timestamp_ms() -> int:
        """Return current time as milliseconds since epoch (int).

        Matches Robot_Hub `GetCurrentTimestamp()` which returns int64 milliseconds.
        """
        return int(time.time() * 1000)

    @staticmethod
    def make_header(
        type_: str,
        protocol_source: Optional[str] = None,
        protocol_category: Optional[str] = None,
        session_id: Optional[str] = None,  # 외부에서 세션 ID를 주입받을 수 있도록 인자 추가
        priority: int = 0,
        version: str = "1.0",
    ) -> Dict[str, Any]:
        """Build a standard message header dict compatible with both projects.

        The returned dict contains both `messageid` (lowercase) and `messageID`
        (camelcase) to maximize compatibility between Robot_Core_Web and Robot_Hub.
        """
        ts = MessageUtils.current_timestamp_ms()
        mid = MessageUtils.generate_uuid()
        
        # 외부에서 넘겨준 세션 ID가 없다면 새로 생성 (이전 질문 피드백 반영)
        final_session_id = session_id if session_id is not None else MessageUtils.generate_uuid()

        header: Dict[str, Any] = {
            "version": version,
            "type": type_,
            "messageid": mid,
            "messageID": mid,          # 상단 주석 명세에 있던 camelCase 호환성 유지
            "sessionid": final_session_id,
            "timestamp": ts,
            "priority": priority,
        }

        if protocol_source is not None:
            header["protocol_source"] = protocol_source

        if protocol_category is not None:
            header["protocol_category"] = protocol_category

        return header