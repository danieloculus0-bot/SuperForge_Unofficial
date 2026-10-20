# SuperForge Unofficial

SuperForge Unofficial is the release-candidate and build-artifact repository for the SuperForge ERP Suite.

## Repo role

This repository is for packaged builds, installer experiments, checksums, manifests, and release-candidate documentation.

Current ERP consolidation source lives in:

- `danieloculus0-bot/Axiom_Beta`

Earlier SuperForge source foundation:

- `danieloculus0-bot/MFGForge`

Source logic being consolidated into the suite comes from:

- `danieloculus0-bot/ForgeQC`
- `danieloculus0-bot/ForgeVault`
- `danieloculus0-bot/MFGForge`

## Current build target

The earlier integration target was:

```text
MFGForge: integration/superforge-suite
```

Current canonical consolidation target: `Axiom_Beta/main`.

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

- `Axiom_Beta` is the current ERP consolidation source.
- `MFGForge` remains an earlier application source line.
- `SuperForge_Unofficial` is the release/artifact repo.

## Portfolio consolidation note (2026-10-20)

**Status: release/artifact planning repository, not a built ERP product.** The inspected tree contains manifests and planning documentation, not a completed application binary or deployment workflow; no GitHub Actions runs appeared in the inspected history. References above to `MFGForge: integration/superforge-suite` identify an **earlier integration direction**. [Axiom Beta](https://github.com/danieloculus0-bot/Axiom_Beta) is the current ERP consolidation target, while [MFGForge](https://github.com/danieloculus0-bot/MFGForge) remains a historical source foundation. A compiled, tested release needs an actual artifact and independently passing installer checks before advertising availability.

[Portfolio audit](https://github.com/danieloculus0-bot/Axiom_Beta/blob/main/docs/PORTFOLIO_AUDIT_2026-10-20.md).
