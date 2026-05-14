# SuperForge Unofficial

SuperForge Unofficial is the release-candidate and build-artifact repository for the SuperForge ERP Suite.

## Repo role

This repository is for packaged builds, installer experiments, checksums, manifests, and release-candidate documentation.

Primary source code lives in:

- `danieloculus0-bot/MFGForge`

Source logic being consolidated into the suite comes from:

- `danieloculus0-bot/ForgeQC`
- `danieloculus0-bot/ForgeVault`
- `danieloculus0-bot/MFGForge`

## Current build target

The integration branch is:

```text
MFGForge: integration/superforge-suite
```

The package target is:

```text
dist/SuperForge.exe
```

## Product goal

One local Windows executable launches one SuperForge ERP Suite containing:

- quality events, RMA, NCR, DMR, CAPA, and deviations
- controlled vendor, supplier, material, purchased part, and document vault logic
- quoting intake, drawing/PDF BOM candidate review, material assignment drafts, and lead-time logic
- planning and purchasing watchlists
- material certificate control
- machine utilization and capacity pressure
- FPY, operator efficiency, quoting throughput, and company pulse reporting
- clean cross-module intelligence and workflow review gates

## Boundary rule

Do not develop primary source code directly in this repository unless the project intentionally migrates here later.

For now:

- `MFGForge` is the source-of-truth app repo.
- `SuperForge_Unofficial` is the release/artifact repo.
