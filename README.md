# SuperForge Unofficial (artifact planning)

Historical release-candidate and artifact-manifest planning repository for the earlier SuperForge line. **This is not a compiled, deployed ERP product.**

## Current build state

**Reviewed:** 2026-10-20 · **Inspected main:** `861d536ea48b`.

**No automated GitHub Actions runs found** at inspection; status is unverified in hosted CI.

[Live CI history](https://github.com/danieloculus0-bot/SuperForge_Unofficial/actions) supersedes this dated report.

## Implemented or recorded today

- Build target and installer/artifact manifest conventions for a possible SuperForge release candidate.
- Context for the earlier `MFGForge` integration direction and a planned release layout.
- Current **Axiom Beta** is the canonical ERP consolidation source, not this repository.

## Run and verification

Read repository planning documents and [the archived original README](docs/archive/README_2026-10-20_before_refresh.md). No verified application executable or standalone launch command is supplied from this repository.

## Known boundaries

- No GitHub Actions run was available at inspection. The planned `dist/SuperForge.exe` path is a target, not a confirmed build artifact.
- Do not advertise app modules, production deployment or a green installer without an actual independent CI job and downloadable asset.

## Next work

Either publish a real, tested Axiom-based artifact pipeline or explicitly retain this repository as historical release planning only.

## References

- [Axiom Beta](https://github.com/danieloculus0-bot/Axiom_Beta)
- [Historical MFGForge](https://github.com/danieloculus0-bot/MFGForge)
- [Complete previous README and historical planning notes](docs/archive/README_2026-10-20_before_refresh.md)
