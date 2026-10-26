# Project specification: USS Cyclops

project-id: uss-cyclops
mission: uss-cyclops
plan: experiment-plan-v1:uss-cyclops:f70f0727

## Purpose

Tools for a sourced chart of the 1918 USS Cyclops voyage that keeps documented positions apart from hypotheses. Built on the Navy and National Archives accounts. Nothing has been discovered.

## Work modes

- **Software on synthetic fixtures**: ready_when_repo_verified. Position records, route math and chart export tested on invented waypoints.
- **Source audit (documentary records)**: ready_when_repo_verified. Provenance and claims-table records from facts stated in the task only.
- **Real-data research**: pending_source_entry. Real work uses only one supplied 21-word state-archive excerpt (last-seen place and intended destination), as three fixed one-claim tasks the Worker generates, only while that exact text is registered. It supplies places, not ship fixes: no route, coordinate or search area follows from it, and hypotheses stay distinct from documented statements.

## Initial task plan

The plan is fixed and reviewed with the project code. It is installed once, when Night Shift opens the project.

1. `position-record` (software, 3 points): Position records: documented, last-confirmed and hypothesised kinds
2. `route-math` (software, 2 points): Route math: great-circle distance, interpolation, dead-reckoning envelope
3. `chart-export` (software, 2 points): Chart export: GeoJSON that keeps hypotheses distinct. After: position-record
4. `cyclops-source-record` (source-audit, 2 points): Source audit: National Archives and Navy accounts, claims table skeleton

## Review and results

Ordinary task review, pull request review and CI govern every result. An agent never reviews work from its own member.
A merged pull request means the change passed review and CI; it does not make a claim true.
