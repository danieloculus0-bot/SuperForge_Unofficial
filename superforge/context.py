from __future__ import annotations

from urllib.parse import urlencode

from .module_registry import context_destinations

def build_context_menu(entity_type: str, entity_id: str = "", context: dict | None = None) -> list[dict]:
    context = dict(context or {})
    if entity_id:
        context.setdefault("entity_id", entity_id)
    context.setdefault("entity_type", entity_type)
    items = []
    for module in context_destinations(entity_type):
        query = urlencode(context)
        items.append({
            "key": module["key"],
            "title": module["title"],
            "area": module["area"],
            "url": module["route"] + (("?" + query) if query else ""),
        })
    return items
