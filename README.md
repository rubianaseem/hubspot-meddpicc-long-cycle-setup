# HubSpot MEDDPICC long-cycle setup (+ readiness agent)

**Set up qualification in HubSpot for long-cycle, multi-stakeholder deals — then audit a deal export for MEDDPICC completeness, single-threading, and security-gate gaps before pipeline review.**

> Built by Rubia Naseem, GTM Engineer (12+ yrs CRM/RevOps, HubSpot & Salesforce).

---

## The pain point

ICP-fit tools assume a fast buying motion. They break when a deal has ~5 stakeholders, a ~6-month evaluation, and legal / procurement / InfoSec as real gates. HubSpot also still makes it hard to see who is missing from the buying committee, so managers discover single-threaded "commit" deals too late.

- *"HubSpot stores all the contacts. But there is no native way to visualize who's in the buying committee, what role each person plays, and critically, who is missing."* ([r/hubspot: HubSpot still has no native buying committee visualization](https://www.reddit.com/r/hubspot/comments/1rh2aig/hubspot_still_has_no_native_buying_committee/))
- *"If the economic buyer never shows up at any stage of a meaningful purchase, that's usually a sign."* ([r/b2b_sales: How do you handle a deal where the economic buyer never actually shows up](https://www.reddit.com/r/b2b_sales/comments/1w38o04/how_do_you_handle_a_deal_where_the_economic_buyer/))

---

## What it gives you

**Playbook (docs)**

- MEDDPICC deal scorecard properties, buying-committee tracking, stage entry requirements, security gate + waiver path
- Rollout order and build checklist in SETUP.md

**Runnable agent (`agent.py`)**

- Audits a sample (or your) HubSpot/Salesforce deal export for MEDDPICC completeness
- Flags single-threaded deals, missing / claimed-only Economic Buyer, untested Champion, blank security gates, stage-entry gaps, stale evidence
- Scores readiness (`ready` / `at_risk` / `not_ready`) and writes a review queue plus CRM-ready field-fill suggestions
- Works with no API key; Claude only sharpens the brief if you set a key
- Never writes to your CRM

---

## Where each step runs

1. **GitHub** holds the playbook and the agent. Clone it or download the ZIP.
2. **A meeting with sales leadership (and InfoSec)** agrees the field set and gates ([SETUP.md rollout](SETUP.md#rollout-order)).
3. **HubSpot sandbox** is where you build properties and stage requirements from [docs/DETAILS.md](docs/DETAILS.md).
4. **Terminal** is where you run `python agent.py` on a deal export before pipeline review.
5. **You, then HubSpot.** AEs fill gaps; managers use the review queue. Optional import of agreed suggestion values only.

**Nothing here auto-fills MEDDPICC judgment fields in the CRM.**

---

## Quick start

**Agent (no HubSpot required for the sample):**

```bash
git clone https://github.com/rubianaseem/hubspot-meddpicc-long-cycle-setup.git
cd hubspot-meddpicc-long-cycle-setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python agent.py            # sample_long_cycle_deals.csv, no API key needed
```

**Playbook:** confirm Sales Hub Pro/Enterprise, then follow the [rollout order](SETUP.md#rollout-order) and property tables in [docs/DETAILS.md](docs/DETAILS.md).

---

## Example output

```text
[NOT_READY] Lumen Defense - Command Suite  (£420,000, Proposal, owner Priya Shah)
    score      : 25/100  completeness 40%  motion=long_cycle
    flags      : single_threaded; missing_economic_buyer; blank_security_gate; ...

[AT_RISK] Northwind Analytics - Enterprise Platform  (£180,000, Negotiation, ...)
    flags      : stage_entry_gap:security still in progress; ...
```

Files in `out/`: `meddpicc_audit.csv`, `review_queue.csv`, `crm_field_suggestions.csv`, `readiness_brief.md`.

---

## Playbook + agent together

Build the HubSpot properties and stage gates once (SETUP.md). Then export open long-cycle deals weekly and run the agent before pipeline review. The review queue is the meeting artefact; the CRM suggestions file is a proposal only. AEs still own MEDDPICC judgment — the agent just makes empty fields impossible to ignore.

## More

- [SETUP.md](SETUP.md): rollout order, build checklist, how to export deals for the agent
- [docs/DETAILS.md](docs/DETAILS.md): full property tables, gates, workflows, views
- [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md): how the agent scores a deal
