from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol

@dataclass
class CanonicalRecord:
    entity_type: str
    external_id: str
    source_system: str
    payload: dict[str, Any]
    links: dict[str, str] = field(default_factory=dict)

class ERPAdapter(Protocol):
    adapter_name: str
    def health(self) -> dict[str, Any]: ...
    def pull(self, entity_type: str, since: str | None = None) -> Iterable[CanonicalRecord]: ...
    def push(self, record: CanonicalRecord) -> dict[str, Any]: ...

class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ERPAdapter] = {}

    def register(self, adapter: ERPAdapter) -> None:
        self._adapters[adapter.adapter_name] = adapter

    def get(self, name: str) -> ERPAdapter:
        return self._adapters[name]

    def list(self) -> list[str]:
        return sorted(self._adapters)

registry = AdapterRegistry()

CANONICAL_ENTITIES = (
    "customer","supplier","part","revision","work_order","operation",
    "purchase_order","purchase_order_line","inventory_item","inventory_transaction",
    "material","material_lot","job_clocking","clocking_error","shipment",
    "quote","quality_event","machine","employee_reference","document_reference"
)

SUPPORTED_TRANSPORTS = (
    "csv_xlsx_flat_file",
    "rest_api",
    "webhook",
    "read_only_database_view",
    "sftp_drop",
    "scheduled_report_import",
)

VENDOR_PROFILES = (
    "JobBOSS2","Epicor","Plex","SAP","SyteLine","Infor","NetSuite","Dynamics365","CustomERP"
)
