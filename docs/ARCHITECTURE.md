# Unified Architecture

```text
                         +----------------------+
                         |   SuperForge Shell   |
                         | dark/light + context |
                         +----------+-----------+
                                    |
                          universal context router
                                    |
      +-----------+-----------+-----+-----+-----------+-----------+
      |           |           |           |           |           |
    Jobs         POs      Inventory    Quality       PM        Vault/FAI
      |           |           |           |           |           |
      +-----------+-----------+-----+-----+-----------+-----------+
                                    |
                              domain event bus
                                    |
                     +--------------+--------------+
                     |                             |
                event ledger                  audit journal
             SQLite relational              JSONL hash chain
                     |                             |
                     +--------------+--------------+
                                    |
                         workflow/action engine
                                    |
                +-------------------+-------------------+
                |                                       |
           ERP adapters                           BEAN learning
    flatfile / REST / SQL / outbox         observations / proposals
                |                                       |
        reconciliation receipts                 human review gate
```

## Transaction boundary

Authoritative records and event routing are deterministic. Learning is advisory.

## Audit boundary

A business mutation is not considered complete until its journal write succeeds. Derived actions retain the originating event/correlation identity.

## Integration boundary

External systems never become hidden second sources of truth. Every import has a sync run. Every external row has a durable external reference. Every outbound write is queued/reconciled and receives a receipt or retry state.

## Context boundary

Every module can accept `context_type` and `context_id`. Direct relationships are used to filter the destination when possible. No blank re-search should be required for common cross-module navigation.
