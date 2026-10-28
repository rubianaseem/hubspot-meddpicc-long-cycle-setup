# Details: HubSpot MEDDPICC long-cycle setup

The full playbook that used to sit in the main README, kept here so the README stays short. The rollout order and build checklist are in [SETUP.md](../SETUP.md). Back to the [README](../README.md).

## Background

How to set up qualification in HubSpot for **long-cycle, multi-stakeholder** deals (e.g. aerospace, defense, anything with a security review).

Assumes hybrid PLG + SLG. Keep the PLG pipeline light. Apply this build to the **sales-assist / enterprise** pipeline (or a dedicated long-cycle pipeline).

## The problem this solves (full version)

Most GitHub / open-source “qualification” tools in GTM lists are strong at:

- firmographic ICP fit
- inbound triage
- enrichment and CRM hygiene

They assume a **fast, self-serve buying motion**.

They break when the deal has:

- ~5 stakeholders
- a ~6-month evaluation
- legal, procurement, and InfoSec as real gates

**Bottom line:** HubSpot (with a real MEDDPICC scorecard and stage gates) is the qualification engine. Other tools feed evidence and milestones into it. Do not ask a single inbound “fit verdict” to replace buying-committee and paper-process qualification.

## Architecture: four lanes (+ optional fifth)

Treat these as **one deal process in HubSpot**, plus optional add-ons. You do not need to buy four products on day one.

### 1. Deal scorecard (start here — pure HubSpot)

This is the qualification engine. Everything else feeds it.

#### Deal properties to create (MEDDPICC)

| Property (suggested internal name) | Type (suggested) | Purpose |
| --- | --- | --- |
| `meddpicc_metrics` | Multi-line text | What success looks like for the buyer |
| `meddpicc_economic_buyer` | Single-line text or association note | Budget owner; prefer also associating the Contact |
| `meddpicc_decision_criteria` | Multi-line text | How they will choose |
| `meddpicc_decision_process` | Multi-line text | Steps, approvers, sequence |
| `meddpicc_paper_process` | Multi-line text | Legal, procurement, InfoSec — critical for A&D |
| `meddpicc_identified_pain` | Multi-line text | Business pain tied to urgency |
| `meddpicc_champion` | Single-line text | Named champion |
| `meddpicc_champion_tested` | Dropdown: Unknown / Claimed / Tested | Influence actually verified |
| `meddpicc_competition` | Multi-line text or checkbox | Alternatives including do-nothing |
| `meddpicc_completeness_pct` | Number (manual or calculated if you have ops support) | Pipeline hygiene signal |

Also associate **Champion** and **Economic Buyer** as deal contacts with roles where your HubSpot plan supports contact roles on deals.

> **Plan note:** custom deal properties, stage entry requirements, and workflows require **Sales Hub Pro or Enterprise** (contact roles on deals need Sales Hub Enterprise). Confirm your tier before building this out — Starter won't support the gates below.

#### Buying committee (multi-stakeholder tracking)

Champion and Economic Buyer are not the whole committee. A 5-stakeholder, 6-month deal typically also has a technical evaluator, an InfoSec/security reviewer, procurement, legal, and an exec sponsor. Track them explicitly — don't let "we have a champion" stand in for "the room is covered."

| Property (suggested internal name) | Type (suggested) | Purpose |
| --- | --- | --- |
| `meddpicc_stakeholder_map` | Multi-line text (or a custom object if you have the tier for it) | Name + role + engagement level for each known stakeholder |
| `meddpicc_stakeholder_count` | Number | How many distinct stakeholders are identified and engaged |
| `meddpicc_single_threaded` | Checkbox / Yes-No | Flag if the deal has only one real contact — the highest-risk state on a long-cycle deal |

Associate each stakeholder as a deal contact with a role (Technical Evaluator, InfoSec Reviewer, Procurement, Legal, Exec Sponsor, etc.) where your plan supports contact roles. If it doesn't, log them in `meddpicc_stakeholder_map` as a running list.

Add a saved view: **open long-cycle deals with fewer than 3 associated stakeholder roles** — this catches single-threaded deals before they stall in late stage, which is the #1 way long-cycle B2B deals silently die.

#### Wire into the pipeline

1. Put the MEDDPICC fields on the deal record layout (deal card / sidebar / focused view so AEs see them without hunting).
2. Build a **pipeline view** (or board columns) that surfaces incompleteness: Champion tested, EB named, Paper process started, Completeness %.
3. Add **stage entry requirements** (examples — adjust names to the client’s stages):

| Moving into / past | Minimum required |
| --- | --- |
| Out of Discovery / Qualify | Champion named + Identified pain |
| Into Proposal / Commercial | Economic Buyer + Decision process |
| Into Negotiation / Late stage | Paper process started (not blank) |
| Into Closed Won (optional hard gate) | Security status Cleared *or* explicit waiver property |

4. Tie **forecast category** or manager review to completeness (even a simple “red if completeness under X% in late stage” view is enough).

This lane is HubSpot-native. No Gong or Accord required to start.

---

### 2. Evidence (keep the scorecard honest)

Empty MEDDPICC fields filled with optimism are worse than blanks.

#### Light version (HubSpot only)

- Require a logged call or note before `meddpicc_champion_tested` = Tested (process rule + training; enforce with workflow tasks if helpful).
- Property: `last_qualification_evidence_date` (date) — updated when AE logs evidence.
- Deal view filter: late-stage deals with stale evidence date.

#### Full version

- Connect Gong (or Chorus / ZoomInfo CI) to HubSpot.
- Map deal-board / MEDDICC playbook suggestions into the **same** MEDDPICC properties where possible.
- Rule: AE owns the field. Conversation intel suggests. Do not silently overwrite without a defined process.

Add this when deals are long and teams inflate “we have a champion.”

---

### 3. Shared timeline (buyer calendar, not just yours)

Multi-stakeholder + six months means someone owns the **buyer’s** milestones.

#### Light version (HubSpot)

Deal-associated tasks or a checklist object (custom object if you use one; otherwise tasks + deal properties):

Examples:

- Security packet sent
- Security / InfoSec call booked
- Legal redlines started
- Procurement intro
- Exec sponsor meeting

Each item: owner + due date. Pipeline view or report on **overdue** items for open late-stage deals.

#### Full version

- Accord or Dock as the mutual action plan the buyer sees.
- Sync key milestones back to HubSpot deal properties or tasks so RevOps keeps one scoreboard.

**Rule:** Do not buy a MAP tool to paper over empty CRM fields. Get MEDDPICC adoption first.

---

### 4. Security gate (InfoSec is qualification)

For aerospace / defense / security-review deals, InfoSec is not a checkbox at the end. It is a gate.

#### HubSpot properties

| Property | Type | Values (example) |
| --- | --- | --- |
| `security_questionnaire_status` | Dropdown | Not started / In progress / Submitted / Cleared / Waived |
| `trust_center_shared` | Checkbox or Yes/No | Packet / trust center shared with buyer |
| `security_blocker_notes` | Multi-line text | What’s stuck |

#### Stage gate

- Cannot move past a defined stage until status ≠ Not started (early enforcement), **or**
- Cannot enter late stage / Closed Won until Cleared or Waived (hard enforcement).

Pick enforcement strength with sales + InfoSec. Document the waiver path so deals do not get stuck forever without an owner.

#### Automation (sketch)

- When Paper process mentions security / when stage hits X: create task for SE/CS (or security owner) to send packet or open questionnaire workspace.
- When status → Cleared: optional Slack/internal notification (draft only until approved).

#### Outside HubSpot

HyperComply, Conveyor, Whistic (or similar) do the questionnaire grind. HubSpot tracks whether the gate is open or blocked. Seller-side GRC (Vanta, Drata, Comp AI compliance, Hyperproof, etc.) is separate from CRM qualification but often pairs with the trust packet.

---

### 5. Optional fifth: account prioritization

**6sense / Demandbase (or similar)** answer: which accounts to chase.

They do **not** answer: is this opportunity qualified.

- Feed target accounts / intent into company score or list membership in HubSpot.
- SDR/AE uses it for coverage.
- MEDDPICC on the deal still decides if the opportunity is real.

Do not mix “account is in-market” with “we have an Economic Buyer.”

## What not to force from self-serve / GitHub GTM tools

| Useful for | Not a substitute for |
| --- | --- |
| ICP / firmographic fit | Champion testing |
| Enrichment waterfalls | Economic Buyer access |
| Inbound “verdict” / lead score | Paper process / InfoSec |
| MCP CRM research agents | Multi-threaded coverage over months |
| PQL / product-usage scoring | Decision process and timeline ownership |

Use HubSpot MCP, Twenty, Comp AI CRM, n8n, OpenOutreach-style kits as **assistive layers** (research, CRM updates, briefs). Do not treat them as the source of truth for deal qualification.

## Workflows & views (optional)

**Not required for v1.** Properties + deal views + stage entry requirements do most of the work. Add workflows (and a few saved views) only where people skip the process without a nudge.

### Principle

Automate **reminders and gates**, not **judgment**.

Do **not** build workflows that auto-fill MEDDPICC from forms, enrichment, or AI. That recreates the PLG “fake qualified” problem.

### Phase 1 (no workflows)

- MEDDPICC + security deal properties
- Deal record layout + pipeline views
- Stage entry requirements (this is the main enforcement)
- Manager ritual: weekly pipeline review on incompleteness

### Phase 2 workflows (add when pain shows up)

#### 1. Late-stage incomplete MEDDPICC

- **Trigger:** deal enters Proposal / Negotiation (use your stage names) AND any of: Champion tested ≠ Tested, Economic Buyer empty, Paper process empty
- **Action:** create task for AE (optional: notify manager). Do not write the qualification fields automatically.

#### 2. Security gate kickoff

- **Trigger:** Paper process populated, OR deal hits a defined stage, OR deal type / pipeline = long-cycle
- **Action:** if `security_questionnaire_status` is blank, set to Not started; create task for security / SE owner (“send packet / open questionnaire workspace”)

#### 3. Stale evidence

- **Trigger:** late-stage deal AND `last_qualification_evidence_date` older than N days (e.g. 14)
- **Action:** task to AE: “log call evidence or update Champion / EB”

#### 4. Security cleared → unblock

- **Trigger:** `security_questionnaire_status` → Cleared
- **Action:** complete related blocker task; optional internal note or Slack draft (send only with approval)

### Saved views (prefer over contact lists)

The unit of work is the **deal**. Use saved pipeline / deal views. Classic contact active lists are secondary.

| View / filter | Purpose |
| --- | --- |
| Open long-cycle deals, completeness under threshold | Pipeline hygiene |
| Open long-cycle deals with under 3 stakeholder roles | Single-threaded deal risk |
| Late-stage + security Not started or In progress | InfoSec bottleneck queue |
| Champion tested = Claimed (not Tested) | Manager coaching |
| Overdue deal tasks (security, legal, procurement) | Timeline slippage |
| Closed-lost with Paper process blank | Post-mortem pattern |

### What to skip

- Contact lifecycle workflows as a substitute for deal MEDDPICC
- Mass sequence enrollment based on “qualified”
- Scoring workflows that collapse ICP fit + MEDDPICC into one number
- Anything that marks a deal qualified without a human updating Champion / EB / Paper process

## Minimal stack (opinionated)

**Must have**

- HubSpot deals + MEDDPICC properties + stage gates

**Add when pain shows up**

- Gong (evidence) and/or Accord/Dock (shared plan)
- HyperComply / Conveyor / Whistic (security packet velocity)

**Optional**

- 6sense / Demandbase for account prioritization

**Assistive only**

- HubSpot MCP, enrichment, n8n, open-source ICP scorers

## One-line takeaway

The open-source GTM “qualification” layer is mostly **PLG/ICP triage + CRM glue**. For long-cycle, security-gated, multi-stakeholder deals, the real engine is **MEDDPICC-in-HubSpot + evidence + shared milestones + security-questionnaire status** — with ABM intent as account prioritization, not deal health.


## Readiness agent

Pair this playbook with `agent.py`. It audits an export against the same MEDDPICC ideas (Champion, Economic Buyer, paper process, security gate, single-threading) and writes local review files. It does not replace stage entry requirements in HubSpot — it catches gaps before the meeting.
