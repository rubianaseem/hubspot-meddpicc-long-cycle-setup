# Walkthrough: MEDDPICC readiness scoring

This follows `agent.py` on `sample_long_cycle_deals.csv` with no API key.

## 1. Column mapping

`ALIASES` accepts HubSpot and Salesforce header variants so you can drop an export in without renaming every column.

## 2. Motion detection

Pipeline name hints mark `long_cycle` vs `light` (sales-assist / PLG). Light-motion deals are still scored, but flagged so you do not force full enterprise gates onto self-serve.

## 3. Completeness

Eight MEDDPICC fields plus Champion Tested and Security Status drive `completeness_pct`. Blank, `n/a`, `unknown`, and `tbd` count as empty.

## 4. Risk flags

- **Single-threaded:** <=1 associated contact (and stakeholder maps that say "only")
- **Economic Buyer claimed-only:** text like "aligned" / "never met" without meeting evidence
- **Champion untested:** named but tested status blank/No
- **Stage-entry gaps:** required fields for the current stage from `STAGE_REQUIREMENTS`
- **Security gate:** blank or blocked on late-stage long-cycle deals
- **Stale evidence:** last evidence date older than `--stale-days` (default 45)

## 5. Readiness band

Start from completeness, then subtract for single-threading, EB/Champion problems, stage gaps, and security issues. Bands: `ready`, `at_risk`, `not_ready`.

## 6. Outputs

`review_queue.csv` is the meeting artefact. `crm_field_suggestions.csv` is a *proposal* file — humans accept values before any HubSpot import. The playbook in SETUP.md / DETAILS.md remains the source of truth for which properties to create.
