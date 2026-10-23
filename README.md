# HubSpot MEDDPICC long-cycle setup

**How to set up qualification in HubSpot for long-cycle, multi-stakeholder deals (e.g. aerospace, defense, anything with a security review).**

> Built by Rubia Naseem, GTM Engineer (12+ yrs CRM/RevOps, HubSpot & Salesforce).

---

## 🧠 The pain point

Most GitHub and open-source "qualification" tools in GTM lists are strong at firmographic ICP fit, inbound triage and CRM hygiene. They assume a fast, self-serve buying motion, and they break when the deal has ~5 stakeholders, a ~6-month evaluation, and legal, procurement and InfoSec as real gates. My view: HubSpot, with a real MEDDPICC scorecard and stage gates, is the qualification engine, and other tools feed evidence and milestones into it.

---

## ✨ What it gives you

- **A MEDDPICC deal scorecard:** the deal properties to create, with suggested internal names, types and purpose
- **Buying-committee tracking:** a stakeholder map, stakeholder count and a single-threaded flag, plus a view that catches single-threaded deals early
- **Stage entry requirements:** what must be filled before a deal moves into each stage
- **A security gate:** InfoSec questionnaire status as a real gate, with a documented waiver path
- **Optional phase 2 workflows and saved views** that automate reminders and gates, not judgment
- **A rollout order and build checklist** you can work through in a sandbox

It assumes hybrid PLG + SLG: keep the PLG pipeline light and apply this to the sales-assist / enterprise (or a dedicated long-cycle) pipeline.

---

## 🗺 Where each step runs

1. **GitHub** is where you read the playbook. There's no code to install.
2. **A meeting with sales leadership (and InfoSec)** is where you agree the MEDDPICC fields, stage names and gates.
3. **A HubSpot sandbox** is where you build the properties, deal views and stage entry requirements, piloted on one long-cycle pipeline.
4. **Your weekly pipeline review** is where managers check completeness, so an empty field means "we don't know".
5. **HubSpot production**, then optional add-ons (Gong, a mutual action plan tool, a questionnaire tool) only once the process is sticking.

**Nothing here auto-fills MEDDPICC fields.** AEs own the judgment.

---

## 🚀 Quick start

1. Check your tier: custom deal properties, stage entry requirements and workflows need **Sales Hub Pro or Enterprise** (contact roles on deals need Enterprise).
2. Follow the [rollout order](SETUP.md#rollout-order) in SETUP.md.
3. Build in a sandbox using the [property tables](docs/DETAILS.md#1-deal-scorecard-start-here--pure-hubspot) in docs/DETAILS.md.
4. Tick off the [build checklist](SETUP.md#build-checklist) as you go.

---

## 📋 Example: stage entry requirements

Adjust the names to your own stages:

| Moving into / past | Minimum required |
| --- | --- |
| Out of Discovery / Qualify | Champion named + Identified pain |
| Into Proposal / Commercial | Economic Buyer + Decision process |
| Into Negotiation / Late stage | Paper process started (not blank) |
| Into Closed Won (optional hard gate) | Security status Cleared *or* explicit waiver property |

---

## 📚 More

- [SETUP.md](SETUP.md): plan note, rollout order and the full build checklist
- [docs/DETAILS.md](docs/DETAILS.md): the full playbook: the four lanes (scorecard, evidence, shared timeline, security gate) plus optional account prioritization, what not to force from self-serve GTM tools, workflows and saved views, the minimal stack, and the one-line takeaway
