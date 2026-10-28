# Setup: HubSpot MEDDPICC long-cycle setup

How to roll this out and what to tick off as you build it. The full playbook (every property, gate, workflow and view) is in [docs/DETAILS.md](docs/DETAILS.md). Back to the [README](README.md).

> **Plan note:** custom deal properties, stage entry requirements, and workflows require **Sales Hub Pro or Enterprise** (contact roles on deals need Sales Hub Enterprise). Confirm your tier before building this out — Starter won't support the gates below.

## Rollout order

1. **Align** on the MEDDPICC field set + stage gates with sales leadership (and InfoSec for security status rules). One session. Get written agreement on stage names and required fields.
2. **Sandbox build:** properties, deal views, stage requirements. Pilot on **one** pipeline (long-cycle only).
3. **Enable AEs:** empty field means “we don’t know,” not “N/A.” Managers review completeness in pipeline meetings.
4. **Security lane:** add status properties + gates for the long-cycle segment only. Leave PLG / SMB pipeline lighter.
5. **Only then:** Gong field mapping and/or MAP tool if the process is sticking.
6. **Last:** ABM intent platforms if TAM is large enough to need account prioritization at scale.

## Build checklist

### Properties

- [ ] MEDDPICC deal properties created (table above)
- [ ] Champion tested dropdown
- [ ] Completeness % (manual OK for v1)
- [ ] Stakeholder map + count + single-threaded flag (buying committee)
- [ ] Security questionnaire status + trust center + blocker notes
- [ ] Optional: last qualification evidence date

### Layout and views

- [ ] Deal record shows MEDDPICC without scrolling forever
- [ ] Pipeline view for long-cycle: Champion tested, EB, Paper process, Security status, Completeness
- [ ] Overdue timeline / task view for late-stage deals

### Process enforcement

- [ ] Stage entry requirements documented and configured
- [ ] Waiver path for security Cleared vs Waived
- [ ] Forecast or manager ritual uses completeness (not vanity stage)

### Segmenting motions

- [ ] Long-cycle pipeline (or deal type) identified
- [ ] PLG / self-serve pipeline explicitly **not** forced onto full MEDDPICC
- [ ] Lists/reports labeled PLG vs SLG where both exist

### Integrations (later)

- [ ] Gong/Chorus mapped to same properties (optional)
- [ ] Accord/Dock sync plan (optional)
- [ ] Questionnaire tool chosen; HubSpot only tracks gate status
- [ ] ABM intent → company lists (optional)


### Workflows & views (optional / phase 2)

- [ ] Late-stage incomplete MEDDPICC → AE task (no auto-fill)
- [ ] Security gate kickoff → status + owner task
- [ ] Stale evidence reminder (if evidence date property exists)
- [ ] Security Cleared → clear blocker / notify
- [ ] Saved deal views: low completeness, security bottleneck, Champion claimed-only
- [ ] Confirmed: no workflow auto-writes MEDDPICC judgment fields

### Enablement

- [ ] One-pager for AEs: what each field means + example good answers
- [ ] Manager scorecard for weekly pipeline review
- [ ] Sandbox → prod change log


## Deal export for the readiness agent

After properties exist (or using the sample file), export open deals from the long-cycle pipeline with the MEDDPICC fields plus `pipeline`, `stage`, `amount`, `owner`, `number of associated contacts`, and security status.

```bash
python agent.py --input ~/Downloads/long_cycle_deals.csv --output out/pipeline-review
```

Outputs stay local: audit CSV, review queue, field-fill suggestions, readiness brief. Import suggestion values only after an AE or manager accepts them. The agent never writes to HubSpot.

Optional Claude: copy `.env.example` to `.env`, set `ANTHROPIC_API_KEY`, re-run. Use `--no-llm` to force rules.
