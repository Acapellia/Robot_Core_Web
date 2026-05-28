"""
Utilities for creating message IDs and timestamps compatible with Robot_Hub.

Provides:
- `generate_uuid()` : RFC4122 UUID4 string
- `current_timestamp_ms()` : integer milliseconds since epoch
- `make_header(...)` : convenience to build a protocol header dict including
  `messageid`/`messageID` and `timestamp` fields (keeps both casing variants)
"""
from __future__ import annotations

import time
import uuid
from typing import Optional, Dict, Any


def generate_uuid() -> str:
	"""Generate a UUID string (UUID4).

	Matches the semantics of Robot_Hub's `GenerateUuid()` used for messageID.
	"""
	return str(uuid.uuid4())


def current_timestamp_ms() -> int:
	"""Return current time as milliseconds since epoch (int).

	Matches Robot_Hub `GetCurrentTimestamp()` which returns int64 milliseconds.
	"""
	return int(time.time() * 1000)


def make_header(
	type_: str,
	protocol_source: Optional[str] = None,
	protocol_category: Optional[str] = None,
	priority: int = 0,
	session_id: Optional[str] = None,
	version: str = "1.0",
) -> Dict[str, Any]:
	"""Build a standard message header dict compatible with both projects.

	The returned dict contains both `messageid` (lowercase) and `messageID`
	(camelcase) to maximize compatibility between Robot_Core_Web and Robot_Hub.
	"""
	ts = current_timestamp_ms()
	mid = generate_uuid()

	header: Dict[str, Any] = {
		"version": version,
		"type": type_,
		"messageid": mid,
		"timestamp": ts,
		"priority": priority,
	}

	if session_id is not None:
		header["sessionid"] = session_id

	if protocol_source is not None:
		header["protocol_source"] = protocol_source

	if protocol_category is not None:
		header["protocol_category"] = protocol_category

	return header

