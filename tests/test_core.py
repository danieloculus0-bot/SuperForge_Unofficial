from superforge.app import create_app
from superforge.context import build_context_menu
from superforge.erp import CANONICAL_ENTITIES
from superforge.module_registry import MODULE_BY_KEY

def test_universal_context_menu_has_expected_trackers():
    names = {x["key"] for x in build_context_menu("work_order","WO-1")}
    assert {"jobs","purchase-orders","inventory","clocking-errors","quality","fai","audit","bean"} <= names

def test_quality_is_registered():
    assert "quality" in MODULE_BY_KEY
    assert "fai" in MODULE_BY_KEY
    assert "purchase_order" in CANONICAL_ENTITIES

def test_routes_smoke():
    app = create_app({"TESTING": True})
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/quality").status_code == 200
    assert client.get("/api/context-menu?entity_type=work_order&entity_id=WO-1").status_code == 200
    assert client.get("/api/system/capabilities").status_code == 200
