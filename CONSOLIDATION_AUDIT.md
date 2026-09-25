# SuperForge Consolidation Audit

Branch: `unified-intelligent-suite`

## Repositories audited

- BEAN: memory, reasoning, uncertainty, supervised self-optimization and learning concepts.
- ForgeQC: strongest quality transaction logic, CAPA/5-Why, quality pulse, ERP ingest, web NCR reporting, Windows/server packaging and hash-chained audit journal.
- MFGForge: strongest unified manufacturing/ERP chassis, module registry, quoting, supplier/material/capacity logic and cross-module intelligence.
- PM-Tracker: simple PM asset/task/completion model to migrate into the canonical maintenance module.
- EZ_Expedite: occurrence/workflow engine, RMA routing, ownership, due dates, Microsoft 365 routing and escalation patterns.
- EZ-FAIR: drawing extraction, GD&T/tolerance handling, ballooning and FAI workbook generation.
- ForgeVault: revision-controlled manufacturing file vault, release packages, dependency graph, plugins and JobBOSS2 handoff pattern.
- venvWin: packaging/runtime isolation concepts only. It is not a manufacturing business module and should remain an optional deployment/runtime technology.
- SuperForge_Unofficial: previously an artifact/release shell. This branch intentionally becomes the unified source tree.

## Consolidation rules

1. One canonical identity for customer, supplier, part, revision, job, PO, inventory item/lot, operation, machine and document.
2. Every module publishes domain events for meaningful mutations.
3. Every mutation is written to the tamper-evident audit chain with actor, timestamp, reason, before/after, correlation id and source module.
4. Cross-module navigation carries record context. Right-click works on every window, and empty-space right-click opens the global launcher.
5. ERP integrations map external systems into canonical records through adapters rather than contaminating core logic with vendor-specific assumptions.
6. BEAN learns from outcome history and proposes changes. It cannot silently rewrite authoritative transaction logic.
7. Quality is the center of gravity and can drill through to jobs, POs, inventory, suppliers, machines, clocking, drawings, FAI and audit evidence.
8. EZ FAIR is a first-class quality module.
9. Existing repositories remain historical/source references until their logic is fully migrated and regression-tested.
10. No destructive migration is permitted without a recorded migration event and rollback path.

## Immediate migration order

1. MFGForge ERP/schema and module logic.
2. ForgeQC quality workflows, CAPA assistant, Quality Pulse, web/server and audit behaviors.
3. EZ Expedite occurrence/RMA workflow and escalation engine.
4. ForgeVault records, files, revision/dependency/release concepts.
5. EZ FAIR extraction/ballooning/FAI services.
6. PM Tracker machine/task/completion data.
7. BEAN supervised learning, memory and proposal logic.
8. Packaging/runtime polish and optional venvWin deployment experiments.
