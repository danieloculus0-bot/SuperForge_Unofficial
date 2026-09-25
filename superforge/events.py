from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
import uuid

from .audit import record_event

@dataclass(frozen=True)
class DomainEvent:
    name: str
    module: str
    entity_type: str
    entity_id: str
    actor: str = "system"
    reason: str = ""
    before: Any = None
    after: Any = None
    data: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: uuid.uuid4().hex)

Handler = Callable[[DomainEvent], None]

class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def publish(self, event: DomainEvent) -> dict:
        audit_row = record_event(
            "DOMAIN_EVENT",
            event.name,
            module=event.module,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            actor=event.actor,
            reason=event.reason,
            before=event.before,
            after=event.after,
            context=event.data,
            correlation_id=event.correlation_id,
        )
        for handler in self._handlers.get(event.name, []):
            handler(event)
        for handler in self._handlers.get("*", []):
            handler(event)
        return audit_row

bus = EventBus()
