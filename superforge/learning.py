from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .runtime_paths import database_path
from .audit import record_event

SCHEMA = """
CREATE TABLE IF NOT EXISTS learning_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT NOT NULL,
  pattern_key TEXT NOT NULL,
  context_json TEXT NOT NULL,
  outcome TEXT NOT NULL,
  success INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS learning_proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proposal_id TEXT NOT NULL UNIQUE,
  module TEXT NOT NULL,
  title TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  proposed_change TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  validation_plan TEXT NOT NULL,
  rollback_plan TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  reviewed_by TEXT,
  review_notes TEXT,
  created_at TEXT NOT NULL
);
"""

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def remember_outcome(module: str, pattern_key: str, context: dict[str, Any], outcome: str, success: bool, actor: str = "system") -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO learning_observations(module,pattern_key,context_json,outcome,success,created_at) VALUES(?,?,?,?,?,?)",
            (module, pattern_key, json.dumps(context, sort_keys=True), outcome, 1 if success else 0, now),
        )
    record_event("LEARNING_OBSERVATION","remember_outcome",module=module,entity_type="pattern",entity_id=pattern_key,actor=actor,after={"outcome":outcome,"success":success})

def pattern_summary(pattern_key: str) -> dict:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT success, COUNT(*) n FROM learning_observations WHERE pattern_key=? GROUP BY success",
            (pattern_key,),
        ).fetchall()
    counts = {int(r["success"]): int(r["n"]) for r in rows}
    total = counts.get(0,0) + counts.get(1,0)
    return {
        "pattern_key": pattern_key,
        "observations": total,
        "successes": counts.get(1,0),
        "failures": counts.get(0,0),
        "confidence": (counts.get(1,0) / total) if total else None,
    }

def propose_improvement(proposal_id: str, module: str, title: str, evidence: dict, proposed_change: str, risk_level: str, validation_plan: str, rollback_plan: str, actor: str="bean") -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO learning_proposals(proposal_id,module,title,evidence_json,proposed_change,risk_level,validation_plan,rollback_plan,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (proposal_id,module,title,json.dumps(evidence,sort_keys=True),proposed_change,risk_level,validation_plan,rollback_plan,now),
        )
    record_event("LEARNING_PROPOSAL","proposal_created",module=module,entity_type="learning_proposal",entity_id=proposal_id,actor=actor,after={"title":title,"risk_level":risk_level})

def review_proposal(proposal_id: str, status: str, reviewer: str, notes: str) -> None:
    if status not in {"approved_for_sandbox","approved_for_human_execution","revision_requested","deferred","rejected","implemented","validated","rolled_back"}:
        raise ValueError("invalid proposal status")
    with _conn() as conn:
        before = conn.execute("SELECT * FROM learning_proposals WHERE proposal_id=?", (proposal_id,)).fetchone()
        if before is None:
            raise KeyError(proposal_id)
        conn.execute("UPDATE learning_proposals SET status=?, reviewed_by=?, review_notes=? WHERE proposal_id=?", (status,reviewer,notes,proposal_id))
    record_event("LEARNING_REVIEW","proposal_reviewed",module="bean",entity_type="learning_proposal",entity_id=proposal_id,actor=reviewer,before=dict(before),after={"status":status,"notes":notes})

AUTO_EXECUTION_ENABLED = False
