# SuperForge Unified Architecture

## Core spine

```
UI shell
  |
  +-- Universal context router ("Open with")
  |
Canonical domain services
  |
  +-- ERP / Jobs / POs / Inventory / Clocking
  +-- Quality Command Center
  +-- EZ FAIR / Inspection / PPAP
  +-- PM / Equipment
  +-- ForgeVault / Documents
  +-- Expedite / Occurrence workflow
  |
Domain event bus
  |
  +-- Cross-module handlers
  +-- KPI / PPM / FPY / risk signals
  +-- Notifications / workflow routing
  +-- ERP integration adapters
  +-- BEAN outcome memory and proposals
  |
Tamper-evident audit journal
```

## Audit contract

Every significant mutation records:

- source module
- event/action
- entity type and ID
- actor
- UTC timestamp
- reason
- before state
- after state
- correlation ID
- request/workflow context
- previous journal hash
- current entry hash

## Universal context navigation

Every window supports right-click. A specific row/card uses its entity type and ID. Empty space uses the global context.

A work order can therefore open with Job Tracker, Purchase Orders, Inventory, Clocking Errors, Quality, EZ FAIR, PM, Vault, Purchasing, Planning, Quoting, Audit Trail, or BEAN Analysis while carrying the selected work-order context.

## ERP-neutral integration

External ERP systems plug into an adapter contract. Supported transport patterns include CSV/XLSX, REST, webhooks, read-only database/report views, SFTP drops and scheduled reports. Vendor profiles can be created for JobBOSS2, Epicor, Plex, SAP, SyteLine/Infor, NetSuite, Dynamics 365 or a custom ERP.

## Learning boundary

Learning is supervised. SuperForge stores outcomes, detects repeated patterns, computes confidence, and creates improvement proposals with evidence, validation and rollback plans. Production rules remain authoritative until a human-approved change is applied and audited.
