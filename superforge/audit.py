from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .runtime_paths import audit_journal_path

_LOCK = threading.RLock()

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()

def _tail(path: Path) -> tuple[int, str]:
    if not path.exists() or path.stat().st_size == 0:
        return 0, "GENESIS"
    last = None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    if not last:
        return 0, "GENESIS"
    row = json.loads(last)
    return int(row["sequence"]), str(row["entry_hash"])

def record_event(
    event_type: str,
    action: str,
    *,
    module: str,
    entity_type: str = "",
    entity_id: str = "",
    actor: str = "",
    reason: str = "",
    before: Any = None,
    after: Any = None,
    context: dict | None = None,
    correlation_id: str | None = None,
) -> dict:
    path = audit_journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        seq, previous_hash = _tail(path)
        row = {
            "sequence": seq + 1,
            "timestamp_utc": _utc_now(),
            "correlation_id": correlation_id or uuid.uuid4().hex,
            "event_type": event_type,
            "action": action,
            "module": module,
            "entity_type": entity_type,
            "entity_id": str(entity_id or ""),
            "actor": actor or "system",
            "reason": reason,
            "before": before,
            "after": after,
            "context": context or {},
            "previous_hash": previous_hash,
        }
        row["entry_hash"] = _digest(row)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, default=str) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return row

def verify_journal(path: str | Path | None = None) -> dict:
    target = Path(path or audit_journal_path())
    if not target.exists():
        return {"ok": True, "entries": 0, "last_hash": "GENESIS"}
    previous = "GENESIS"
    entries = 0
    with target.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            claimed = row.pop("entry_hash", None)
            if row.get("previous_hash") != previous:
                return {"ok": False, "line": line_no, "error": "previous hash mismatch"}
            calculated = _digest(row)
            if calculated != claimed:
                return {"ok": False, "line": line_no, "error": "entry hash mismatch"}
            previous = claimed
            entries += 1
    return {"ok": True, "entries": entries, "last_hash": previous}

def tail_entries(limit: int = 100) -> list[dict]:
    path = audit_journal_path()
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows[-max(1, min(int(limit), 1000)):]
