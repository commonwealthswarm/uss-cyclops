# Sources

Every real source this project uses or plans to use is listed here with its terms. A source is only used for research
work after the Night Shift operator registers a curated source entry for it. Nothing listed below has been analysed.

## Inventory and blockers

Real-data state: **pending_source_entry** (gate: curated source entry).

Real work uses only one supplied 21-word state-archive excerpt (last-seen place and intended destination), as three fixed one-claim tasks the Worker generates, only while that exact text is registered. It supplies places, not ship fixes: no route, coordinate or search area follows from it, and hypotheses stay distinct from documented statements.

Inventory:
- NC Department of Natural and Cultural Resources, USS Cyclops, Lost at Sea, 1918: 21-word attributed excerpt

Blockers:
- No source with a position, route point or page-cited route record is registered.
- Real-data tasks exist only while the reviewed excerpt is registered with its exact hash.

## Rules

- Do not commit source data files. Records point to sources; they do not copy them (a test enforces this).
- Records built from a description alone are `unverified` and carry no hash.
- A source whose redistribution terms are restricted or unresolved is never marked publishable.
