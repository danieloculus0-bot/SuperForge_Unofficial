from __future__ import annotations
from .db import db

EXTENSION_SCHEMA=r"""
CREATE TABLE IF NOT EXISTS quote_intakes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,quote_number TEXT NOT NULL UNIQUE,customer_id INTEGER REFERENCES customers(id),
  part_id INTEGER REFERENCES parts(id),drawing_document_id INTEGER REFERENCES documents(id),due_date TEXT,status TEXT NOT NULL DEFAULT 'new',
  owner TEXT,estimated_value REAL,lead_time_days INTEGER,material_risk TEXT,capacity_risk TEXT,quality_risk TEXT,notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS planning_watchlists(
  id INTEGER PRIMARY KEY AUTOINCREMENT,job_id INTEGER REFERENCES jobs(id),customer_id INTEGER REFERENCES customers(id),
  source_module TEXT,source_event_id TEXT,risk_type TEXT NOT NULL,risk_level TEXT NOT NULL DEFAULT 'medium',due_date TEXT,owner TEXT,
  signal TEXT NOT NULL,action_required TEXT,status TEXT NOT NULL DEFAULT 'open',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS purchasing_watchlists(
  id INTEGER PRIMARY KEY AUTOINCREMENT,po_id INTEGER REFERENCES purchase_orders(id),supplier_id INTEGER REFERENCES suppliers(id),
  inventory_item_id INTEGER REFERENCES inventory_items(id),source_event_id TEXT,risk_level TEXT NOT NULL DEFAULT 'medium',need_by_date TEXT,
  owner TEXT,signal TEXT NOT NULL,action_required TEXT,status TEXT NOT NULL DEFAULT 'open',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
def init_extensions()->None:
    with db() as con:
        con.executescript(EXTENSION_SCHEMA)
