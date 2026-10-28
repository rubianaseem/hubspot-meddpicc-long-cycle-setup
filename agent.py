#!/usr/bin/env python3
"""
MEDDPICC Deal Readiness Agent
-----------------------------
Audits a HubSpot / Salesforce deal export for MEDDPICC field completeness on
long-cycle deals. Flags single-threaded deals, missing Economic Buyer /
Champion, blank security-gate fields, and stage-entry gaps. Scores readiness
and writes a review queue plus CRM-ready field-fill suggestions (local files
only; never writes to your CRM).

Pairs with the HubSpot setup playbook in SETUP.md and docs/DETAILS.md.

Runs with no API key using built-in rules. If ANTHROPIC_API_KEY is set it asks
Claude to sharpen the pipeline brief, and falls back on any API error.

Usage:
  python agent.py
  python agent.py --input ~/Downloads/deals.csv --output out/
  python agent.py --no-llm
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "sample_long_cycle_deals.csv"
DEFAULT_OUTPUT = HERE / "out"
DEFAULT_MODEL = "claude-sonnet-5-5"

ALIASES = {
    "deal_id": ["deal_id", "record id", "deal id", "opportunity id", "id"],
    "deal_name": ["deal_name", "deal name", "opportunity name", "name"],
    "company": ["company", "associated company", "account name", "account"],
    "owner": ["owner", "deal owner", "opportunity owner"],
    "amount": ["amount", "deal amount", "amount (gbp)", "amount (usd)", "acv", "tcv"],
    "pipeline": ["pipeline", "deal pipeline", "record source pipeline"],
    "stage": ["stage", "deal stage", "opportunity stage"],
    "close_date": ["close_date", "close date", "closedate"],
    "days_in_stage": ["days_in_stage", "days in stage", "hs_v2_date_entered_current_stage"],
    "contacts_engaged": ["contacts_engaged", "number of associated contacts", "num_associated_contacts", "contacts"],
    "metrics": ["metrics", "meddpicc_metrics", "metric", "identified metric"],
    "economic_buyer": ["economic_buyer", "economic buyer", "eb", "budget holder"],
    "decision_criteria": ["decision_criteria", "decision criteria", "dc"],
    "decision_process": ["decision_process", "decision process", "dp"],
    "paper_process": ["paper_process", "paper process", "procurement process"],
    "identify_pain": ["identify_pain", "identify pain", "pain", "identified pain"],
    "champion": ["champion", "meddpicc_champion"],
    "champion_tested": ["champion_tested", "champion tested", "champion strength"],
    "competition": ["competition", "competitor", "competitors"],
    "security_status": ["security_status", "security questionnaire status", "infosec status"],
    "security_blocker_notes": ["security_blocker_notes", "security notes", "infosec notes"],
    "stakeholder_map": ["stakeholder_map", "buying committee", "stakeholders"],
    "last_evidence_date": ["last_evidence_date", "last qualification evidence date", "last meddpicc update"],
    "notes": ["notes", "deal notes", "next step", "description"],
}

# Stage entry requirements (minimum fields that should be non-blank).
STAGE_REQUIREMENTS = {
    "discovery": ["champion", "identify_pain"],
    "qualify": ["champion", "identify_pain"],
    "evaluation": ["champion", "identify_pain", "metrics", "competition"],
    "proposal": ["champion", "economic_buyer", "decision_criteria", "decision_process", "identify_pain"],
    "commercial": ["champion", "economic_buyer", "decision_criteria", "decision_process", "paper_process"],
    "negotiation": ["champion", "economic_buyer", "decision_process", "paper_process", "security_status"],
    "legal/procurement": ["champion", "economic_buyer", "paper_process", "security_status"],
    "legal": ["champion", "economic_buyer", "paper_process", "security_status"],
    "procurement": ["champion", "economic_buyer", "paper_process", "security_status"],
    "closed won": ["champion", "economic_buyer", "security_status"],
}

LONG_CYCLE_PIPELINE_HINTS = ("long-cycle", "enterprise", "strategic", "complex")
LIGHT_PIPELINE_HINTS = ("sales-assist", "plg", "self-serve", "smb", "starter")

FIELD_LABELS = {
    "metrics": "Metrics",
    "economic_buyer": "Economic Buyer",
    "decision_criteria": "Decision Criteria",
    "decision_process": "Decision Process",
    "paper_process": "Paper Process",
    "identify_pain": "Identify Pain",
    "champion": "Champion",
    "champion_tested": "Champion Tested",
    "competition": "Competition",
    "security_status": "Security Status",
}

MEDDPICC_SCORE_FIELDS = [
    "metrics", "economic_buyer", "decision_criteria", "decision_process",
    "paper_process", "identify_pain", "champion", "competition",
]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ and val:
            os.environ[key] = val


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for candidate in (value, value[:10]):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
    return None


def parse_amount(value: str) -> float:
    cleaned = re.sub(r"[^\d.\-]", "", value or "")
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def parse_int(value: str) -> int | None:
    cleaned = re.sub(r"[^\d]", "", value or "")
    return int(cleaned) if cleaned else None


def money(x: float) -> str:
    return f"£{x:,.0f}"


def filled(value: str) -> bool:
    v = (value or "").strip().lower()
    return bool(v) and v not in {"n/a", "na", "none", "unknown", "tbd", "-"}


def read_deals(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        lookup = {h.strip().lower(): h for h in headers}
        mapping = {}
        for field, names in ALIASES.items():
            for name in names:
                if name in lookup:
                    mapping[field] = lookup[name]
                    break
        deals = []
        for raw in reader:
            d = {field: (raw.get(src) or "").strip() for field, src in mapping.items()}
            for field in ALIASES:
                d.setdefault(field, "")
            d["amount_value"] = parse_amount(d.get("amount", ""))
            d["contacts_n"] = parse_int(d.get("contacts_engaged", ""))
            d["days_n"] = parse_int(d.get("days_in_stage", ""))
            d["close"] = parse_date(d.get("close_date", ""))
            d["evidence"] = parse_date(d.get("last_evidence_date", ""))
            deals.append(d)
    return deals


def pipeline_motion(pipeline: str) -> str:
    p = (pipeline or "").lower()
    if any(h in p for h in LIGHT_PIPELINE_HINTS):
        return "light"
    if any(h in p for h in LONG_CYCLE_PIPELINE_HINTS):
        return "long_cycle"
    return "unknown"


def stage_key(stage: str) -> str:
    s = (stage or "").strip().lower()
    for key in STAGE_REQUIREMENTS:
        if key in s:
            return key
    return s


def eb_is_claimed_only(text: str) -> bool:
    t = (text or "").lower()
    if not filled(text):
        return False
    claim_words = ("claimed", "aligned", "never met", "not met", "assures", "assured", "says they")
    met_words = ("met ", "met)", "(met", "joined", "on the call", "attended")
    if any(w in t for w in met_words):
        return False
    return any(w in t for w in claim_words) or "unknown" in t


def security_ok_for_late(status: str) -> bool:
    s = (status or "").strip().lower()
    return s in {"cleared", "waived", "approved", "complete", "completed"}


def audit_deal(deal: dict, stale_days: int) -> dict:
    motion = pipeline_motion(deal.get("pipeline", ""))
    stage = stage_key(deal.get("stage", ""))
    flags: list[str] = []
    suggestions: list[dict] = []

    completeness_fields = MEDDPICC_SCORE_FIELDS + ["champion_tested", "security_status"]
    filled_n = sum(1 for f in completeness_fields if filled(deal.get(f, "")))
    completeness_pct = round(100.0 * filled_n / len(completeness_fields))

    # Core MEDDPICC gaps
    for field in MEDDPICC_SCORE_FIELDS:
        if not filled(deal.get(field, "")):
            flags.append(f"missing_{field}")
            suggestions.append({
                "property": FIELD_LABELS[field],
                "suggested_value": "",
                "reason": f"Blank {FIELD_LABELS[field]} on a {deal.get('stage') or 'open'} deal",
                "priority": "high" if field in ("champion", "economic_buyer", "identify_pain") else "medium",
            })

    contacts_n = deal["contacts_n"] if deal["contacts_n"] is not None else 0
    if contacts_n <= 1:
        flags.append("single_threaded")
    map_text = deal.get("stakeholder_map", "")
    if filled(map_text) and "only" in map_text.lower() and contacts_n <= 1:
        flags.append("stakeholder_map_confirms_single_thread")

    if not filled(deal.get("champion", "")):
        flags.append("missing_champion")
    elif not filled(deal.get("champion_tested", "")):
        flags.append("champion_untested")
        suggestions.append({
            "property": "Champion Tested",
            "suggested_value": "No",
            "reason": "Champion named but tested status blank — treat as untested until proven",
            "priority": "high",
        })
    else:
        tested = deal["champion_tested"].lower()
        if tested.startswith("no") or "untested" in tested:
            flags.append("champion_untested")

    if not filled(deal.get("economic_buyer", "")):
        flags.append("missing_economic_buyer")
    elif eb_is_claimed_only(deal["economic_buyer"]):
        flags.append("economic_buyer_claimed_only")
        suggestions.append({
            "property": "Economic Buyer",
            "suggested_value": deal["economic_buyer"],
            "reason": "EB looks claimed without a meeting — book EB time before late-stage work",
            "priority": "high",
        })

    # Stage entry gaps
    required = STAGE_REQUIREMENTS.get(stage, [])
    stage_gaps = [f for f in required if not filled(deal.get(f, ""))]
    for f in stage_gaps:
        flags.append(f"stage_entry_gap:{f}")

    # Security gate
    late = stage in {"proposal", "commercial", "negotiation", "legal/procurement", "legal", "procurement", "closed won"}
    sec = deal.get("security_status", "")
    if motion == "long_cycle" and late and not filled(sec):
        flags.append("blank_security_gate")
        suggestions.append({
            "property": "Security Status",
            "suggested_value": "Not started",
            "reason": "Late-stage long-cycle deal with blank security status",
            "priority": "high",
        })
    elif motion == "long_cycle" and late and filled(sec) and not security_ok_for_late(sec):
        if sec.lower() in {"blocked", "rejected", "failed"}:
            flags.append("security_blocked")
        else:
            flags.append("security_incomplete")
        if not filled(deal.get("security_blocker_notes", "")):
            flags.append("security_blocker_notes_blank")

    # Stale evidence
    if deal["evidence"] and (date.today() - deal["evidence"]).days >= stale_days:
        flags.append(f"stale_evidence_{(date.today() - deal['evidence']).days}d")
    elif not deal["evidence"] and motion == "long_cycle" and stage not in {"discovery", "qualify"}:
        flags.append("missing_evidence_date")

    if motion == "light":
        flags.append("light_motion_pipeline")
        # Still score, but note full MEDDPICC gates may be overkill

    # Readiness score 0-100
    score = completeness_pct
    if "single_threaded" in flags:
        score -= 15
    if "economic_buyer_claimed_only" in flags or "missing_economic_buyer" in flags:
        score -= 15
    if "champion_untested" in flags or "missing_champion" in flags:
        score -= 10
    if any(f.startswith("stage_entry_gap") for f in flags):
        score -= 10
    if "blank_security_gate" in flags or "security_blocked" in flags:
        score -= 10
    elif "security_incomplete" in flags:
        score -= 5
    if "light_motion_pipeline" in flags:
        score = min(score + 5, 100)  # do not over-penalise PLG
    score = max(0, min(100, score))

    blockers = {
        "single_threaded", "missing_economic_buyer", "economic_buyer_claimed_only",
        "blank_security_gate", "security_blocked", "security_incomplete", "missing_champion",
    }
    if score >= 75 and not any(f.startswith("stage_entry_gap") or f in blockers for f in flags):
        band = "ready"
    elif score >= 45:
        band = "at_risk"
    else:
        band = "not_ready"

    # Suggested fills from notes / stakeholder map when blank
    if not filled(deal.get("champion", "")) and filled(deal.get("stakeholder_map", "")):
        m = re.search(r"champion:\s*([^;]+)", deal["stakeholder_map"], re.I)
        if m:
            suggestions.append({
                "property": "Champion",
                "suggested_value": m.group(1).strip(),
                "reason": "Parsed from stakeholder_map",
                "priority": "medium",
            })

    # Dedup flags
    flags = list(dict.fromkeys(flags))

    return {
        **{k: deal.get(k, "") for k in [
            "deal_id", "deal_name", "company", "owner", "pipeline", "stage", "close_date",
            "metrics", "economic_buyer", "decision_criteria", "decision_process",
            "paper_process", "identify_pain", "champion", "champion_tested", "competition",
            "security_status", "security_blocker_notes", "stakeholder_map", "last_evidence_date", "notes",
        ]},
        "amount": deal["amount_value"],
        "contacts_engaged": contacts_n,
        "days_in_stage": deal["days_n"] if deal["days_n"] is not None else "",
        "motion": motion,
        "completeness_pct": completeness_pct,
        "readiness_score": score,
        "readiness_band": band,
        "flags": "; ".join(flags),
        "stage_gaps": ", ".join(FIELD_LABELS.get(f, f) for f in stage_gaps),
        "suggestions": suggestions,
        "summary": (
            f"{band.replace('_', ' ')} ({score}/100, {completeness_pct}% fields filled). "
            f"Flags: {', '.join(flags) if flags else 'none'}."
        ),
    }


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
        return anthropic.Anthropic()
    except Exception as exc:  # noqa: BLE001
        print(f"  ! Could not init Anthropic client ({exc.__class__.__name__}); using rules only.")
        return None


def _ask(client, model: str, prompt: str, max_tokens: int = 700) -> str:
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [b.text for b in msg.content if getattr(b, "type", "") == "text"]
    return "\n".join(parts).strip()


def template_brief(rows: list[dict]) -> str:
    n = len(rows)
    at_risk = [r for r in rows if r["readiness_band"] == "at_risk"]
    not_ready = [r for r in rows if r["readiness_band"] == "not_ready"]
    single = [r for r in rows if "single_threaded" in r["flags"]]
    eb = [r for r in rows if "missing_economic_buyer" in r["flags"] or "economic_buyer_claimed_only" in r["flags"]]
    sec = [r for r in rows if "blank_security_gate" in r["flags"] or "security_blocked" in r["flags"] or "security_incomplete" in r["flags"]]
    value_risk = sum(r["amount"] for r in not_ready + at_risk)
    return (
        f"Audited {n} deals. {len(not_ready)} not ready and {len(at_risk)} at risk "
        f"({money(value_risk)} combined). {len(single)} are single-threaded, {len(eb)} are missing a real "
        f"Economic Buyer meeting, and {len(sec)} have a security-gate problem. "
        f"Use the review queue before the next pipeline meeting; do not advance stage on deals with stage-entry gaps."
    )


def llm_brief(client, model: str, rows: list[dict]) -> str | None:
    lines = "\n".join(
        f"- {r['deal_name']} | {money(r['amount'])} | {r['stage']} | score {r['readiness_score']} | {r['flags']}"
        for r in rows
    )
    prompt = f"""You are a RevOps lead writing a short MEDDPICC readiness readout for a pipeline review.
Write 4-6 plain sentences. No emojis. Use only this data. Do not invent numbers. Currency GBP.

Deals:
{lines}
"""
    try:
        return _ask(client, model, prompt, 650) or None
    except Exception as exc:  # noqa: BLE001
        print(f"  ! Claude brief failed ({exc.__class__.__name__}); using template brief.")
        return None


def write_outputs(rows: list[dict], brief: str, out_dir: Path, mode: str, source: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_csv = out_dir / "meddpicc_audit.csv"
    review_csv = out_dir / "review_queue.csv"
    suggest_csv = out_dir / "crm_field_suggestions.csv"
    brief_md = out_dir / "readiness_brief.md"

    fields = [
        "deal_id", "deal_name", "company", "owner", "amount", "pipeline", "stage", "motion",
        "contacts_engaged", "completeness_pct", "readiness_score", "readiness_band",
        "stage_gaps", "flags", "champion", "economic_buyer", "security_status", "summary",
    ]
    with audit_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "amount": int(r["amount"]) if float(r["amount"]).is_integer() else r["amount"]})

    with review_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["deal_id", "deal_name", "owner", "stage", "amount",
                                          "readiness_band", "readiness_score", "issue", "priority"])
        w.writeheader()
        for r in rows:
            if r["readiness_band"] == "ready" and not r["flags"]:
                continue
            issues = [x for x in r["flags"].split("; ") if x]
            if not issues:
                issues = [r["readiness_band"]]
            for issue in issues:
                priority = "high" if r["readiness_band"] == "not_ready" or issue in {
                    "single_threaded", "missing_economic_buyer", "economic_buyer_claimed_only",
                    "blank_security_gate", "security_blocked", "missing_champion",
                } or issue.startswith("stage_entry_gap") else "medium"
                w.writerow({
                    "deal_id": r["deal_id"], "deal_name": r["deal_name"], "owner": r["owner"],
                    "stage": r["stage"], "amount": int(r["amount"]) if float(r["amount"]).is_integer() else r["amount"],
                    "readiness_band": r["readiness_band"], "readiness_score": r["readiness_score"],
                    "issue": issue, "priority": priority,
                })

    with suggest_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["deal_id", "deal_name", "property", "suggested_value", "reason", "priority"])
        w.writeheader()
        for r in rows:
            for s in r["suggestions"]:
                w.writerow({"deal_id": r["deal_id"], "deal_name": r["deal_name"], **s})
            # Also emit blank required fields as empty suggestions for CRM import prep
            for gap in (r["stage_gaps"].split(", ") if r["stage_gaps"] else []):
                if gap and not any(s["property"] == gap for s in r["suggestions"]):
                    w.writerow({
                        "deal_id": r["deal_id"], "deal_name": r["deal_name"],
                        "property": gap, "suggested_value": "",
                        "reason": "Required for current stage entry — AE must fill",
                        "priority": "high",
                    })

    md = [
        "# MEDDPICC readiness brief",
        "",
        f"_Source: `{source.name}` · {len(rows)} deals · generated {date.today().isoformat()} · mode: {mode}_",
        "",
        "## Summary",
        "",
        brief,
        "",
        "## Deal scores",
        "",
        "| Deal | Amount | Stage | Score | Band | Top flags |",
        "|---|---:|---|---:|---|---|",
    ]
    for r in sorted(rows, key=lambda x: x["readiness_score"]):
        top = "; ".join(r["flags"].split("; ")[:3]) if r["flags"] else "none"
        md.append(
            f"| {r['deal_name']} | {money(r['amount'])} | {r['stage']} | {r['readiness_score']} | "
            f"{r['readiness_band']} | {top} |"
        )
    md += [
        "",
        "## How to use with the HubSpot playbook",
        "",
        "1. Keep using [SETUP.md](../SETUP.md) rollout order to create the properties and stage gates.",
        "2. Export deals -> run this agent -> review `review_queue.csv` in pipeline meeting.",
        "3. AEs fill gaps in HubSpot themselves (or via import of agreed values from `crm_field_suggestions.csv`).",
        "",
        "---",
        "",
        "_The agent did not write to HubSpot or Salesforce._",
        "",
    ]
    brief_md.write_text("\n".join(md))
    return {"audit": audit_csv, "review": review_csv, "suggestions": suggest_csv, "brief": brief_md}


def main() -> None:
    load_dotenv(HERE / ".env")
    p = argparse.ArgumentParser(description="Audit long-cycle deals for MEDDPICC readiness.")
    p.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--stale-days", type=int, default=int(os.environ.get("MEDDPICC_STALE_DAYS", "45")))
    args = p.parse_args()

    if not args.input.exists():
        sys.exit(f"Input file not found: {args.input}")

    client = None if args.no_llm else get_client()
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    mode = f"Claude ({model})" if client else "built-in rules (no API key)"

    deals = read_deals(args.input)
    rows = [audit_deal(d, args.stale_days) for d in deals]

    bar = "=" * 76
    print(bar)
    print(f" MEDDPICC READINESS AGENT  |  {args.input.name}  |  {len(rows)} deals  |  {mode}")
    print(bar)

    for r in rows:
        tag = r["readiness_band"].upper()
        print(f"\n[{tag}] {r['deal_name']}  ({money(r['amount'])}, {r['stage']}, owner {r['owner'] or '?'})")
        print(f"    score      : {r['readiness_score']}/100  completeness {r['completeness_pct']}%  motion={r['motion']}")
        if r["flags"]:
            print(f"    flags      : {r['flags']}")
        if r["stage_gaps"]:
            print(f"    stage gaps : {r['stage_gaps']}")

    brief = (llm_brief(client, model, rows) if client else None) or template_brief(rows)
    files = write_outputs(rows, brief, args.output, mode, args.input)

    print(f"\n{bar}\n SUMMARY\n{bar}")
    print(brief)
    bands = Counter(r["readiness_band"] for r in rows)
    print("\nBy band:")
    for band, n in bands.most_common():
        print(f"  {band:<12} {n}")
    print(f"\n{bar}\n FILES (nothing was written to your CRM)")
    for label, path in files.items():
        try:
            shown = path.relative_to(Path.cwd())
        except ValueError:
            shown = path
        print(f"  {label:<12} ./{shown}")
    print(bar)
    print("Playbook: see SETUP.md (rollout order) and docs/DETAILS.md (property tables).")


if __name__ == "__main__":
    main()
