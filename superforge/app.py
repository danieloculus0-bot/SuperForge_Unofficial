from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from .audit import tail_entries, verify_journal
from .context import build_context_menu
from .erp import CANONICAL_ENTITIES, SUPPORTED_TRANSPORTS, VENDOR_PROFILES
from .module_registry import MODULES
from .quality import QUALITY_CAPABILITIES
from .runtime_paths import data_root

def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(test_config or {})

    @app.context_processor
    def shared():
        return {"modules": MODULES}

    @app.get("/")
    def home():
        return render_template("shell.html", page_title="Company Pulse", active="company-pulse", page_heading="SuperForge", page_subheading="One auditable manufacturing operating system.")

    @app.get("/quality")
    def quality():
        return render_template("quality.html", page_title="Quality Command Center", active="quality", capabilities=QUALITY_CAPABILITIES)

    @app.get("/quality/<path:subpath>")
    @app.get("/erp/<path:subpath>")
    @app.get("/pm")
    @app.get("/vault")
    @app.get("/fai")
    @app.get("/bean")
    @app.get("/integrations")
    def generic_module(subpath: str | None = None):
        path = request.path
        title = next((m["title"] for m in MODULES if m["route"] == path), path.strip("/").replace("-"," ").title() or "SuperForge")
        return render_template("shell.html", page_title=title, active="", page_heading=title, page_subheading="Context-aware module shell. Data services are consolidated behind the shared event and audit spine.")

    @app.get("/audit")
    def audit():
        return jsonify({"verification": verify_journal(), "entries": tail_entries(100)})

    @app.get("/api/context-menu")
    def context_menu():
        entity_type = request.args.get("entity_type","global")
        entity_id = request.args.get("entity_id","")
        context = {k:v for k,v in request.args.items() if k not in {"entity_type","entity_id"}}
        return jsonify(build_context_menu(entity_type, entity_id, context))

    @app.get("/api/system/capabilities")
    def capabilities():
        return jsonify({
            "modules": MODULES,
            "quality": QUALITY_CAPABILITIES,
            "erp": {
                "canonical_entities": CANONICAL_ENTITIES,
                "transports": SUPPORTED_TRANSPORTS,
                "vendor_profiles": VENDOR_PROFILES,
            },
            "data_root": str(data_root()),
            "learning_auto_execution": False,
        })

    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5080, debug=False)
