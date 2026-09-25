from __future__ import annotations

MODULES = [
    {"key":"company-pulse","title":"Company Pulse","area":"Intelligence","route":"/"},
    {"key":"quality","title":"Quality Command Center","area":"Quality","route":"/quality"},
    {"key":"ncr","title":"NCR / DMR","area":"Quality","route":"/quality/ncr"},
    {"key":"capa","title":"CAR / CAPA","area":"Quality","route":"/quality/capa"},
    {"key":"rma","title":"RMA / Customer Complaints","area":"Quality","route":"/quality/rma"},
    {"key":"deviations","title":"Deviation Control","area":"Quality","route":"/quality/deviations"},
    {"key":"ppap","title":"PPAP / APQP","area":"Quality","route":"/quality/ppap"},
    {"key":"fai","title":"EZ FAIR / FAI","area":"Quality","route":"/fai"},
    {"key":"inspection","title":"Inspection Planning","area":"Quality","route":"/quality/inspection"},
    {"key":"supplier-quality","title":"Supplier Quality","area":"Quality","route":"/quality/suppliers"},
    {"key":"jobs","title":"Job Tracker","area":"ERP","route":"/erp/jobs"},
    {"key":"purchase-orders","title":"Purchase Order Tracker","area":"ERP","route":"/erp/purchase-orders"},
    {"key":"inventory","title":"Inventory Tracker","area":"ERP","route":"/erp/inventory"},
    {"key":"clocking-errors","title":"Job Clocking Error Reporting","area":"ERP","route":"/erp/clocking-errors"},
    {"key":"purchasing","title":"Purchasing Watchlist","area":"ERP","route":"/erp/purchasing"},
    {"key":"planning","title":"Planning Watchlist","area":"ERP","route":"/erp/planning"},
    {"key":"quotes","title":"Quoting","area":"ERP","route":"/erp/quotes"},
    {"key":"suppliers","title":"Supplier Master","area":"ERP","route":"/erp/suppliers"},
    {"key":"customers","title":"Customer Master","area":"ERP","route":"/erp/customers"},
    {"key":"pm","title":"Preventive Maintenance","area":"Maintenance","route":"/pm"},
    {"key":"vault","title":"Drawing / Document Vault","area":"Documents","route":"/vault"},
    {"key":"bean","title":"BEAN Analysis","area":"Intelligence","route":"/bean"},
    {"key":"audit","title":"Audit Trail","area":"System","route":"/audit"},
    {"key":"integrations","title":"ERP Integrations","area":"System","route":"/integrations"},
]

MODULE_BY_KEY = {m["key"]: m for m in MODULES}

ENTITY_RELEVANCE = {
    "work_order": ["jobs","purchase-orders","inventory","clocking-errors","quality","fai","pm","vault","purchasing","planning","quotes","audit","bean"],
    "purchase_order": ["purchase-orders","inventory","supplier-quality","suppliers","jobs","quality","audit","bean"],
    "inventory_item": ["inventory","purchase-orders","purchasing","jobs","quality","supplier-quality","audit","bean"],
    "clocking_error": ["clocking-errors","jobs","quality","pm","planning","audit","bean"],
    "part": ["jobs","inventory","purchase-orders","quality","fai","vault","quotes","supplier-quality","audit","bean"],
    "quality_event": ["quality","ncr","capa","rma","deviations","ppap","fai","jobs","purchase-orders","inventory","vault","audit","bean"],
    "machine": ["pm","jobs","clocking-errors","quality","planning","audit","bean"],
    "supplier": ["suppliers","purchase-orders","inventory","supplier-quality","purchasing","quality","audit","bean"],
    "drawing": ["vault","fai","ppap","inspection","jobs","quotes","quality","audit","bean"],
    "global": [m["key"] for m in MODULES],
}

def context_destinations(entity_type: str) -> list[dict]:
    keys = ENTITY_RELEVANCE.get(entity_type, ENTITY_RELEVANCE["global"])
    return [MODULE_BY_KEY[k] for k in keys if k in MODULE_BY_KEY]
