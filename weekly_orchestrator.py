#!/usr/bin/env python3
"""
ENIL Weekly Agentic Orchestration Workflow  v1.0.0
===================================================
Run every Monday morning. This is the intelligence review,
compounding loop, and decision engine for the entire ENIL system.

Framework:
  Thiel  → monopoly signals, secret-finding, moat measurement
  Taleb  → antifragility scan, chaos-to-value conversion

Five Phases:
  1. INTELLIGENCE SCAN     — what changed across all monitored sources
  2. CONTENT QUEUE         — what to write/update this week (prioritised)
  3. REVENUE PIPELINE      — B2B prospect status and follow-up triggers
  4. SYSTEM OPTIMISATION   — data freshness, moat scores, SEO health
  5. REPORT GENERATION     — JSON + Markdown report → obsidian vault

Usage:
  python weekly_orchestrator.py                # full run
  python weekly_orchestrator.py --phase 1      # single phase
  python weekly_orchestrator.py --dry-run      # no writes, print only
  python weekly_orchestrator.py --skip-pipeline # skip data pipeline re-run

Cron (add to crontab for local automation):
  0 6 * * 1  cd /path/to/enil-data && python weekly_orchestrator.py >> logs/weekly.log 2>&1

GitHub Actions: add to .github/workflows/weekly_orchestration.yml
  schedule: "0 4 * * 1"  (04:00 UTC = 06:00 SAST, every Monday)
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

# ─── Logging ──────────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/weekly_orchestrator.log", mode="a"),
    ],
)
log = logging.getLogger("ENIL.weekly")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE          = Path(__file__).parent
DATA          = BASE / "pipeline" / "data"
RUNS          = BASE / "pipeline" / "runs"
WEEKLY_REPORTS= BASE / "weekly_reports"
OBSIDIAN      = BASE / "obsidian"
REVENUE_FILE  = BASE / "revenue_pipeline.json"

WEEKLY_REPORTS.mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# ─── Constants ────────────────────────────────────────────────────────────────
SCHEMA_VERSION = "1.0.0"
BCOM_MEDIAN    = 23_000     # ZAR/month — benchmark for salary comparisons
DATA_STALE_WARN= 7          # days before a data source triggers a warning
DATA_STALE_CRIT= 14         # days before critical stale flag


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def week_id() -> str:
    iso = datetime.now().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def next_monday() -> date:
    today = date.today()
    return today + timedelta(days=(7 - today.weekday()))

def load_json(path: Path, default=None):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def days_since(path: Path) -> int:
    if not path.exists():
        return 9999
    return (date.today() - date.fromtimestamp(path.stat().st_mtime)).days

def sep(char="═", width=62):
    log.info(char * width)

def phase_header(n: int, title: str):
    sep()
    log.info(f"  PHASE {n}: {title}")
    sep()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — INTELLIGENCE SCAN
# What changed in the past 7 days across all monitored sources?
# Every piece of chaos is a content event.
# ══════════════════════════════════════════════════════════════════════════════

def phase_1_intelligence_scan() -> dict:
    phase_header(1, "INTELLIGENCE SCAN")

    report = {
        "week":          week_id(),
        "scan_date":     datetime.now().isoformat(),
        "nsfas":         _scan_nsfas(),
        "dbe":           _scan_dbe(),
        "aps":           _scan_aps(),
        "labour":        _scan_labour(),
        "seo":           _scan_seo(),
        "opportunities": [],   # filled by antifragility scan
    }

    report["opportunities"] = _antifragility_scan(report)
    _print_intel_summary(report)
    return report


def _scan_nsfas() -> dict:
    log.info("\n► NSFAS scan...")
    result = {
        "portal_up":       None,
        "current_state":   None,
        "new_alerts_7d":   0,
        "critical_active": False,
        "portal_status_code": None,
    }

    # Portal health check
    try:
        import requests
        r = requests.get("https://mynsfas.nsfas.org.za", timeout=12)
        result["portal_up"]          = (r.status_code == 200)
        result["portal_status_code"] = r.status_code
        icon = "✅" if result["portal_up"] else "🔴"
        log.info(f"    myNSFAS portal: {icon}  HTTP {r.status_code}")
    except Exception as e:
        result["portal_up"] = False
        log.warning(f"    myNSFAS portal: ❌ UNREACHABLE — {e}")

    # Current state
    state_file = DATA / "nsfas" / "current_state.json"
    if state_file.exists():
        data = load_json(state_file)
        result["current_state"] = data.get("current_state")
        log.info(f"    Current state:  {result['current_state']}")

    # Recent alerts
    alerts_file = DATA / "nsfas" / "alerts.json"
    if alerts_file.exists():
        alerts   = load_json(alerts_file, [])
        cutoff   = datetime.now() - timedelta(days=7)
        recent   = [a for a in alerts
                    if datetime.fromisoformat(a.get("published_at","2000-01-01")) > cutoff]
        result["new_alerts_7d"]   = len(recent)
        result["critical_active"] = any(a.get("severity") == "critical" for a in recent)
        log.info(f"    Alerts (7d):    {result['new_alerts_7d']} | Critical: {result['critical_active']}")

    return result


def _scan_dbe() -> dict:
    log.info("\n► DBE scan...")
    result = {
        "new_docs_7d":   0,
        "matric_season": False,
        "data_age_days": days_since(DATA / "dbe" / "pass_rates.csv"),
    }

    month = datetime.now().month
    result["matric_season"] = month in (10, 11, 12, 1)

    manifest = load_json(DATA / "dbe" / "doc_manifest.json", {"docs": []})
    cutoff   = date.today() - timedelta(days=7)
    recent   = [d for d in manifest["docs"]
                if date.fromisoformat(d.get("found","2000-01-01")) > cutoff]
    result["new_docs_7d"] = len(recent)

    log.info(f"    New docs (7d):  {result['new_docs_7d']}")
    log.info(f"    Matric season:  {'⚠️  YES — monitor daily' if result['matric_season'] else 'No'}")
    log.info(f"    Data age:       {result['data_age_days']} days")
    return result


def _scan_aps() -> dict:
    log.info("\n► APS scan...")
    result = {
        "total_programmes":    0,
        "new_prospectuses_7d": 0,
        "data_age_days":       days_since(DATA / "aps" / "aps_requirements.csv"),
    }

    import csv
    aps_file = DATA / "aps" / "aps_requirements.csv"
    if aps_file.exists():
        with open(aps_file) as f:
            result["total_programmes"] = sum(1 for _ in csv.DictReader(f))

    manifest = load_json(DATA / "aps" / "prospectus_manifest.json", {"prospectuses": {}})
    cutoff   = date.today() - timedelta(days=7)
    new_ones = [p for p in manifest["prospectuses"].values()
                if date.fromisoformat(p.get("found","2000-01-01")) > cutoff]
    result["new_prospectuses_7d"] = len(new_ones)

    log.info(f"    Programmes DB:  {result['total_programmes']}")
    log.info(f"    New prospectus: {result['new_prospectuses_7d']} (7d)")
    log.info(f"    Data age:       {result['data_age_days']} days")
    return result


def _scan_labour() -> dict:
    log.info("\n► Labour market scan...")
    result = {
        "total_occupations":  0,
        "critical_shortages": 0,
        "top_gaps":           [],
        "data_age_days":      days_since(DATA / "labour" / "demand_gap.json"),
    }

    gap_file = DATA / "labour" / "demand_gap.json"
    if gap_file.exists():
        data = load_json(gap_file)
        rows = data.get("rows", [])
        result["total_occupations"]  = len(rows)
        result["critical_shortages"] = sum(1 for r in rows if r.get("demand_signal") == "CRITICAL_SHORTAGE")
        result["top_gaps"]           = [
            {"occ": r["occupation"], "gap": r["demand_gap"], "signal": r["demand_signal"]}
            for r in rows[:5]
        ]

    log.info(f"    Occupations:    {result['total_occupations']}")
    log.info(f"    Critical gaps:  {result['critical_shortages']}")
    log.info(f"    Data age:       {result['data_age_days']} days")

    if result["top_gaps"]:
        log.info("    Top gaps:")
        for g in result["top_gaps"][:3]:
            log.info(f"      {g['occ']:<30} gap={g['gap']:+d}  [{g['signal']}]")
    return result


def _scan_seo() -> dict:
    log.info("\n► SEO scan...")
    result = {"site_reachable": False, "notes": []}

    try:
        import requests
        r = requests.get("https://enil.co.za", timeout=12)
        result["site_reachable"] = (r.status_code == 200)
        log.info(f"    enil.co.za:     {'✅ Live' if result['site_reachable'] else '❌ Unreachable'} (HTTP {r.status_code})")
    except Exception:
        log.warning("    enil.co.za:     ❌ Not reachable (DNS not yet configured?)")
        result["notes"].append("Domain not live — check GitHub Pages and DNS settings")

    result["notes"].append("Google Search Console API integration pending — add GSC_API_KEY to .env")
    return result


def _antifragility_scan(report: dict) -> list:
    """
    Talebian core:
    Map chaos events → content actions → subscriber acquisition moments.
    Every NSFAS crisis is a content event.
    Every DBE delay is a search spike.
    """
    log.info("\n► Antifragility scan (chaos → value)...")
    opportunities = []

    nsfas  = report["nsfas"]
    dbe    = report["dbe"]
    labour = report["labour"]

    # NSFAS portal down
    if nsfas.get("portal_up") is False:
        opportunities.append({
            "type":             "NSFAS_PORTAL_DOWN",
            "severity":         "CRITICAL",
            "talebian_value":   "HIGH — portal failures generate 3–5× normal search volume",
            "content_action":   "Publish portal-down alert on all WhatsApp channels NOW. Update /nsfas/ page with alternative submission steps.",
            "seo_action":       "Add crisis banner to NSFAS pages. Target: 'NSFAS portal not working 2025'.",
            "newsletter_action":"Send emergency Beehiiv brief: 'NSFAS portal is down — what to do right now'.",
            "effort_hours":     1.5,
            "priority":         1,
        })

    # Active crisis
    if nsfas.get("critical_active"):
        opportunities.append({
            "type":             "NSFAS_ACTIVE_CRISIS",
            "severity":         "HIGH",
            "talebian_value":   "HIGH — crisis queries spike 2–3× baseline",
            "content_action":   "Update appeals template library. Publish rejection-code plain-language guide.",
            "seo_action":       "Add current-crisis banner to all NSFAS state pages. Update meta descriptions with current year.",
            "newsletter_action":"Next Beehiiv issue lead story: NSFAS crisis explainer.",
            "effort_hours":     2.5,
            "priority":         1,
        })

    # New NSFAS alerts
    if nsfas.get("new_alerts_7d", 0) > 0:
        opportunities.append({
            "type":             "NEW_NSFAS_ALERTS",
            "severity":         "MEDIUM",
            "talebian_value":   "MEDIUM — new circulars generate targeted search queries",
            "content_action":   f"Decode {nsfas['new_alerts_7d']} new alert(s) in plain language. Publish as standalone pages.",
            "seo_action":       f"Create dedicated page per new circular. Target: 'NSFAS circular {date.today().year}'.",
            "newsletter_action":"Include in next Navigation Brief.",
            "effort_hours":     1.5,
            "priority":         2,
        })

    # Matric season
    if dbe.get("matric_season"):
        opportunities.append({
            "type":             "MATRIC_SEASON_ACTIVE",
            "severity":         "HIGH",
            "talebian_value":   "MEDIUM — predictable annual spike, high volume, high parent anxiety",
            "content_action":   "Publish/update subject choice guide for Grade 10 parents. Update credential trap pages.",
            "seo_action":       f"Update all credential-trap page meta with '{date.today().year}'. Boost APS calculator internal links.",
            "newsletter_action":"Matric season special edition: subject choice guide.",
            "effort_hours":     3.0,
            "priority":         2,
        })

    # Critical labour shortages
    if labour.get("critical_shortages", 0) >= 3:
        opportunities.append({
            "type":             "LABOUR_SHORTAGE_SIGNAL",
            "severity":         "MEDIUM",
            "talebian_value":   "MEDIUM — gap data is B2B sales content AND SEO asset simultaneously",
            "content_action":   "Update Ekurhuleni map gap table. Add salary comparison vs BCom for top 3 shortage occupations.",
            "seo_action":       "Publish occupation-specific pages: 'electrician jobs Ekurhuleni 2025', 'millwright vacancies Springs'.",
            "newsletter_action":"Feature 'The Artisan Advantage' in next issue with salary data.",
            "effort_hours":     2.0,
            "priority":         3,
        })

    log.info(f"    Opportunities:  {len(opportunities)} detected")
    for o in opportunities:
        log.info(f"      [{o['severity']}] {o['type']}")
    return opportunities


def _print_intel_summary(report: dict):
    log.info("\n" + "─" * 62)
    log.info("  INTELLIGENCE BRIEF SUMMARY")
    log.info("─" * 62)
    n = report["nsfas"]
    log.info(f"  NSFAS portal:   {'UP' if n.get('portal_up') else 'DOWN / UNREACHABLE'}")
    log.info(f"  Current state:  {n.get('current_state','unknown').replace('_',' ').title()}")
    log.info(f"  Crisis active:  {n.get('critical_active', False)}")
    log.info(f"  Opportunities:  {len(report['opportunities'])} antifragile events")
    log.info("─" * 62)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — CONTENT PRODUCTION QUEUE
# Prioritised weekly content queue — urgent first, then scheduled rotation
# ══════════════════════════════════════════════════════════════════════════════

SPRINT_ROTATION = {
    1: {
        "task":     "Credential Trap Detector — add 3 new subject combinations",
        "type":     "data_content",
        "platform": ["GitHub Pages", "Beehiiv"],
        "effort_h": 3.0,
        "priority": 2,
        "details":  "Target combinations: PHY+MATH+EGD (Class D optimal), TOUR+MATL+BUS (Class A trap), IT+MATH+LIFES (Class C invisible).",
    },
    2: {
        "task":     "NSFAS State Machine — review and update all 6 state pages",
        "type":     "intelligence_update",
        "platform": ["GitHub Pages"],
        "effort_h": 2.0,
        "priority": 2,
        "details":  "Check current state data. Update 'Current Crisis Alert' section on each page. Add latest rejection codes.",
    },
    3: {
        "task":     "Ekurhuleni Map — refresh vacancy counts from PNet/LinkedIn",
        "type":     "data_refresh",
        "platform": ["GitHub Pages"],
        "effort_h": 4.0,
        "priority": 2,
        "details":  "Run labour_scraper.py --live. Cross-check top 5 occupations against MERSETA data. Regenerate gap table.",
    },
    4: {
        "task":     "SEO Sprint — 5 new keyword-targeted pages + GSC submission",
        "type":     "seo_content",
        "platform": ["GitHub Pages", "Google Search Console"],
        "effort_h": 5.0,
        "priority": 3,
        "details":  "Target: 'NSFAS appeal letter template', 'APS for nursing 2025', 'Springs TVET college courses', 'Ekurhuleni apprenticeship 2025', 'NSFAS R07 rejection code'.",
    },
}

STANDING_TASKS = [
    {
        "task":     "WhatsApp broadcast — weekly plain-language navigation brief",
        "type":     "distribution",
        "platform": ["WhatsApp Springs", "WhatsApp Germiston", "WhatsApp Kempton Park"],
        "effort_h": 1.0,
        "priority": 2,
        "details":  "Max 3 paragraphs. Lead with the most urgent current issue (NSFAS state / matric deadlines / new vacancy data). Trilingual: English + Zulu summary + Sotho summary.",
    },
    {
        "task":     "Revenue pipeline — follow up 1 SETA contact + 1 recruiter",
        "type":     "revenue",
        "platform": ["Email"],
        "effort_h": 1.0,
        "priority": 2,
        "details":  "Check revenue_pipeline.json for overdue follow-ups. Advance one prospect from 'identified' to 'contacted'.",
    },
]

MONTHLY_TASKS = [
    {
        "task":     "Beehiiv Navigation Brief — monthly edition",
        "type":     "newsletter",
        "platform": ["Beehiiv", "Substack mirror"],
        "effort_h": 2.5,
        "priority": 2,
        "details":  "Lead story: most urgent NSFAS/DBE/labour insight this month. Sections: Crisis Alert / Credential Trap of the Month / Gap Table Spotlight / Revenue Note (for institutional subscribers).",
    },
    {
        "task":     "Data pipeline audit — verify all sources, check for stale data",
        "type":     "infrastructure",
        "platform": ["GitHub Actions"],
        "effort_h": 1.5,
        "priority": 3,
        "details":  "Run python pipeline/pipeline.py --source all. Review runs/ log. Check GitHub Actions logs for failures.",
    },
]


def phase_2_content_queue(intel: dict) -> dict:
    phase_header(2, "CONTENT PRODUCTION QUEUE")

    queue = {"urgent": [], "this_week": [], "backlog": [], "total_effort_h": 0.0}

    # Urgent: antifragile opportunities → immediate content
    for opp in intel.get("opportunities", []):
        if opp["severity"] in ("CRITICAL", "HIGH") and opp["priority"] == 1:
            queue["urgent"].append({
                "task":      opp["content_action"],
                "type":      "crisis_content",
                "platform":  ["WhatsApp", "Beehiiv", "GitHub Pages"],
                "effort_h":  opp["effort_hours"],
                "priority":  1,
                "seo_note":  opp["seo_action"],
            })
        else:
            queue["this_week"].append({
                "task":     opp["content_action"],
                "type":     "opportunity_content",
                "platform": ["GitHub Pages"],
                "effort_h": opp["effort_hours"],
                "priority": opp["priority"],
            })

    # Scheduled sprint rotation (week mod 4)
    week_slot = datetime.now().isocalendar()[1] % 4 + 1
    sprint    = SPRINT_ROTATION[week_slot]
    queue["this_week"].append(sprint)

    # Standing weekly tasks
    queue["this_week"].extend(STANDING_TASKS)

    # Monthly tasks — only on first Monday of month
    if date.today().day <= 7:
        queue["this_week"].extend(MONTHLY_TASKS)
        log.info("  ℹ  First Monday of month — monthly tasks added")

    # Calculate total effort
    all_tasks = queue["urgent"] + queue["this_week"]
    queue["total_effort_h"] = sum(t["effort_h"] for t in all_tasks)

    # Print
    log.info(f"\n  Week: {week_id()}")
    if queue["urgent"]:
        log.info(f"\n  🔴 URGENT ({len(queue['urgent'])} tasks):")
        for t in queue["urgent"]:
            log.info(f"     [{t['effort_h']}h] {t['task'][:70]}")

    log.info(f"\n  📅 THIS WEEK ({len(queue['this_week'])} tasks):")
    for t in sorted(queue["this_week"], key=lambda x: x["priority"]):
        log.info(f"     [{t['effort_h']}h] {t['task'][:70]}")

    log.info(f"\n  ⏱  Total effort: {queue['total_effort_h']}h this week")
    return queue


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — REVENUE PIPELINE
# B2B prospect tracking + overdue follow-up alerts
# ══════════════════════════════════════════════════════════════════════════════

INITIAL_PIPELINE = {
    "created":       date.today().isoformat(),
    "year_target_r": 215_000,
    "currency":      "ZAR",
    "prospects": [
        # SETAs
        {"id":"P001","name":"MERSETA Gauteng Region",        "type":"SETA",        "stage":"identified","value_r":12000,"product":"B2B Data Intelligence Report (quarterly)","notes":"Artisan gap data directly matches MERSETA mandate. Priority contact.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        {"id":"P002","name":"EWSETA",                         "type":"SETA",        "stage":"identified","value_r":10000,"product":"B2B Data Intelligence Report (quarterly)","notes":"Electrical sector — high match with Springs/Germiston data.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        # Recruiters
        {"id":"P003","name":"Scaw Metals (Springs)",          "type":"Recruiter",   "stage":"identified","value_r":5000,"product":"Monthly TVET Talent Pipeline Report","notes":"Springs plant — direct consumer of electrical/mech graduates.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        {"id":"P004","name":"Rand Refinery (Germiston)",      "type":"Recruiter",   "stage":"identified","value_r":5000,"product":"Monthly TVET Talent Pipeline Report","notes":"Artisan-heavy workforce — instrumentation and electrical.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        {"id":"P005","name":"OR Tambo Logistics Cluster",     "type":"Recruiter",   "stage":"identified","value_r":4000,"product":"Monthly TVET Talent Pipeline Report","notes":"Kempton Park zone — logistics and aviation maintenance.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        # Private schools
        {"id":"P006","name":"St Dunstan's College (Benoni)",  "type":"PrivateSchool","stage":"identified","value_r":12000,"product":"Premium Navigation Brief (annual)","notes":"Grade 9–12 subject choice mapping + parent evening deck.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        {"id":"P007","name":"Edenglen High (Edenvale)",       "type":"PrivateSchool","stage":"identified","value_r":12000,"product":"Premium Navigation Brief (annual)","notes":"Edenvale corridor — strong parent community engagement.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        {"id":"P008","name":"Boksburg High School",           "type":"PrivateSchool","stage":"identified","value_r":10000,"product":"Premium Navigation Brief (annual)","notes":"Large Grade 9-10 cohort. TVET pathway messaging relevant.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        # TVET colleges — highest unit economics
        {"id":"P009","name":"Springs TVET College",           "type":"TVETCollege", "stage":"identified","value_r":33000,"product":"Employment Outcomes Dashboard (R25k setup + R8k/yr)","notes":"Priority 1. Springs plant cluster = perfect demand match for their engineering graduates.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        {"id":"P010","name":"Ekurhuleni West TVET College",   "type":"TVETCollege", "stage":"identified","value_r":33000,"product":"Employment Outcomes Dashboard (R25k setup + R8k/yr)","notes":"Largest in corridor. Political visibility for principal.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
        {"id":"P011","name":"Ekurhuleni East TVET College",   "type":"TVETCollege", "stage":"identified","value_r":33000,"product":"Employment Outcomes Dashboard (R25k setup + R8k/yr)","notes":"Germiston base — strong engineering + business programmes.","contact_name":None,"contact_email":None,"next_follow_up":None,"last_contact":None},
    ],
    # Outreach templates
    "templates": {
        "seta": {
            "subject": "Ekurhuleni Artisan Demand Data — ENIL Intelligence Report",
            "body": (
                "Dear [Name],\n\n"
                "I've been tracking artisan vacancy data across the Ekurhuleni corridor "
                "(Springs, Germiston, Kempton Park) and cross-referencing it against TVET "
                "graduate output from your sector.\n\n"
                "The gap is significant: [X] vacancies vs [Y] annual graduates from Ekurhuleni "
                "TVET colleges in your sector. I've structured this data in a format that "
                "could directly support your learnership funding allocation decisions.\n\n"
                "I'd like to show you a sample report. 15 minutes via Teams or phone?\n\n"
                "[Your name] | ENIL Navigation Intelligence | enil.co.za"
            ),
        },
        "tvet_college": {
            "subject": "Employment Outcomes Data for [College Name] — Demonstration",
            "body": (
                "Dear Principal [Name],\n\n"
                "ENIL has been tracking live vacancy data across the Ekurhuleni industrial "
                "corridor — specifically for the programmes your college offers.\n\n"
                "The short version: your Electrical Engineering graduates face [X] open "
                "positions in the Springs/Germiston zone right now. This data exists publicly "
                "— your college just doesn't have it formatted in a way that communicates "
                "your employment outcomes to prospective learners or to DHET.\n\n"
                "We build Employment Outcomes Dashboards for TVET colleges. I'd like to show "
                "you a prototype specifically for [College Name]'s programmes.\n\n"
                "Available for a 20-minute call this week?\n\n"
                "[Your name] | ENIL | enil.co.za/ekurhuleni-map/"
            ),
        },
        "private_school": {
            "subject": "Subject Choice Intelligence for [School Name] — Grade 9 Parent Evening",
            "body": (
                "Dear [Name],\n\n"
                "I produce the ENIL Navigation Brief — a structured intelligence layer that "
                "maps matric subject combinations against university APS requirements, NSFAS "
                "eligibility, and Ekurhuleni labour market demand.\n\n"
                "For [School Name], this would mean: a subject-by-subject mapping report for "
                "every combination offered at your school, plus a branded Career Trajectory "
                "Deck for your Grade 9 parent evening — formatted to your school's brand.\n\n"
                "Would a conversation be worthwhile? I'm happy to share a sample report.\n\n"
                "[Your name] | ENIL | enil.co.za"
            ),
        },
    },
}

STAGE_ORDER = ["identified", "contacted", "demo_scheduled", "proposal_sent", "negotiating", "won", "lost"]


def phase_3_revenue_pipeline() -> dict:
    phase_header(3, "REVENUE PIPELINE REVIEW")

    # Load or initialise pipeline
    if not REVENUE_FILE.exists():
        save_json(INITIAL_PIPELINE, REVENUE_FILE)
        log.info("  Revenue pipeline initialised with 11 prospects")

    pipeline = load_json(REVENUE_FILE)
    prospects = pipeline.get("prospects", [])

    # ── Metrics ──
    total_value      = sum(p.get("value_r", 0) for p in prospects)
    by_stage         = {}
    for p in prospects:
        by_stage.setdefault(p.get("stage","unknown"), []).append(p)

    won_value        = sum(p.get("value_r",0) for p in by_stage.get("won", []))
    pipeline_value   = total_value - won_value
    year_target      = pipeline.get("year_target_r", 215_000)
    pct_to_target    = round(won_value / year_target * 100, 1)

    log.info(f"\n  Year target:      R{year_target:,}")
    log.info(f"  Won to date:      R{won_value:,}  ({pct_to_target}% of target)")
    log.info(f"  Open pipeline:    R{pipeline_value:,}")
    log.info(f"\n  Pipeline by stage:")
    for stage in STAGE_ORDER:
        prps = by_stage.get(stage, [])
        if prps:
            stage_val = sum(p.get("value_r",0) for p in prps)
            log.info(f"    {stage:<20} {len(prps):>2} prospects  R{stage_val:>8,}")

    # ── Overdue follow-ups ──
    today   = date.today()
    overdue = [
        p for p in prospects
        if p.get("next_follow_up")
        and date.fromisoformat(p["next_follow_up"]) <= today
        and p.get("stage") not in ("won","lost")
    ]

    if overdue:
        log.info(f"\n  ⚠️  OVERDUE FOLLOW-UPS ({len(overdue)}):")
        for p in overdue:
            log.info(f"    [{p['id']}] {p['name']} ({p['type']}) — due {p['next_follow_up']}")
    else:
        log.info("\n  ✅  No overdue follow-ups")

    # ── Weekly revenue action ──
    # Identify the highest-priority prospect not yet contacted
    not_contacted = [p for p in prospects if p.get("stage") == "identified"]
    if not_contacted:
        priority_types = ["TVETCollege", "SETA", "Recruiter", "PrivateSchool"]
        for ptype in priority_types:
            candidates = [p for p in not_contacted if p.get("type") == ptype]
            if candidates:
                rec = candidates[0]
                log.info(f"\n  📌 RECOMMENDED ACTION THIS WEEK:")
                log.info(f"     Contact: {rec['name']} ({rec['type']})")
                log.info(f"     Product: {rec['product']}")
                log.info(f"     Value:   R{rec['value_r']:,}")
                log.info(f"     Note:    {rec['notes']}")
                tpl_key = {"TVETCollege":"tvet_college","SETA":"seta","PrivateSchool":"private_school","Recruiter":"seta"}.get(ptype,"seta")
                tpl = pipeline.get("templates",{}).get(tpl_key,{})
                if tpl:
                    log.info(f"     Template subject: {tpl.get('subject','')}")
                break

    result = {
        "year_target_r":  year_target,
        "won_r":          won_value,
        "pipeline_r":     pipeline_value,
        "pct_to_target":  pct_to_target,
        "by_stage":       {k: len(v) for k,v in by_stage.items()},
        "overdue_count":  len(overdue),
        "total_prospects":len(prospects),
    }
    return result


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — SYSTEM OPTIMISATION
# Data freshness · moat scores · SEO health · infrastructure checks
# ══════════════════════════════════════════════════════════════════════════════

def phase_4_optimisation() -> dict:
    phase_header(4, "SYSTEM OPTIMISATION")

    result = {
        "data_freshness":   {},
        "moat_scores":      {},
        "antifragility":    0,
        "optimisations":    [],
        "github_actions":   {},
    }

    # ── Data freshness ──
    log.info("\n► Data freshness audit:")
    sources = {
        "dbe":    DATA / "dbe"    / "pass_rates.csv",
        "nsfas":  DATA / "nsfas"  / "alerts.json",
        "aps":    DATA / "aps"    / "aps_requirements.csv",
        "labour": DATA / "labour" / "demand_gap.json",
    }
    for src, path in sources.items():
        age = days_since(path)
        result["data_freshness"][src] = age
        icon = "✅" if age <= DATA_STALE_WARN else "⚠️" if age <= DATA_STALE_CRIT else "🔴"
        log.info(f"    {src:<10} {icon}  {age} days old")
        if age > DATA_STALE_WARN:
            severity = "CRITICAL" if age > DATA_STALE_CRIT else "WARNING"
            result["optimisations"].append({
                "type":     f"STALE_DATA_{src.upper()}",
                "severity": severity,
                "age_days": age,
                "action":   f"python pipeline/pipeline.py --source {src}",
            })

    # ── Moat scores (Thielian framework) ──
    log.info("\n► Moat assessment (Thielian framework):")
    result["moat_scores"] = _score_moats(result["data_freshness"])
    for name, score in result["moat_scores"].items():
        bar  = "█" * score + "░" * (10 - score)
        log.info(f"    {name:<20} [{bar}] {score}/10")

    # ── Antifragility score ──
    result["antifragility"] = _score_antifragility()
    af_bar = "█" * result["antifragility"] + "░" * (10 - result["antifragility"])
    log.info(f"\n  Antifragility:       [{af_bar}] {result['antifragility']}/10")
    log.info("  (10 = system fully benefits from NSFAS/DBE disorder)")

    # ── GitHub Actions health ──
    log.info("\n► GitHub Actions check (verify manually):")
    result["github_actions"] = {
        "data_monitor_url":   "https://github.com/ENIL-ZA/enil-data/actions/workflows/data_monitor.yml",
        "site_rebuild_url":   "https://github.com/ENIL-ZA/enil-site/actions/workflows/site_rebuild.yml",
        "last_run_check":     "Visit URLs above → confirm last run succeeded (green ✅)",
    }
    log.info(f"    data_monitor.yml: {result['github_actions']['data_monitor_url']}")
    log.info(f"    site_rebuild.yml: {result['github_actions']['site_rebuild_url']}")

    # ── Optimisation summary ──
    if result["optimisations"]:
        log.info(f"\n  ⚠️  {len(result['optimisations'])} optimisation action(s) required:")
        for o in result["optimisations"]:
            log.info(f"    [{o['severity']}] {o['type']} — run: {o['action']}")
    else:
        log.info("\n  ✅  All systems nominal")

    return result


def _score_moats(freshness: dict) -> dict:
    """Score each moat dimension 1–10 based on current system state."""
    scores = {}

    # Data moat: quality and breadth of the schema
    data_score = 2  # baseline
    if (DATA / "aps"    / "aps_requirements.csv").exists(): data_score += 2
    if (DATA / "labour" / "demand_gap.json").exists():      data_score += 3  # the killer asset
    if (DATA / "nsfas"  / "state_machine.json").exists():   data_score += 2
    if (DATA / "dbe"    / "subject_performance.csv").exists(): data_score += 1
    # Cross-reference capability (all 4 sources present)
    if all(v <= 14 for v in freshness.values() if v < 9999): data_score = min(data_score + 1, 10)
    scores["Data Moat"] = min(data_score, 10)

    # Distribution moat: grows with newsletter + WhatsApp + backlinks
    # Manual estimation — replace with GSC API data when available
    scores["Distribution Moat"] = 2  # start: site live, no traffic yet

    # Trust moat: grows with accuracy + community presence
    scores["Trust Moat"] = 3   # start: initial content published

    # SEO moat: grows with indexed pages + backlinks
    scores["SEO Moat"] = 1    # start: not yet indexed

    return scores


def _score_antifragility() -> int:
    """
    Antifragility: does the system BENEFIT from NSFAS/DBE disorder?
    Architecture is inherently antifragile. Grows toward 10 as automation
    converts crisis events into content automatically.
    """
    score = 7  # Architecture is antifragile by design
    # +1 when NSFAS alerts auto-publish to site
    # +1 when WhatsApp automation triggers on portal-down events
    # +1 when crisis events auto-generate newsletter drafts
    return score


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — REPORT GENERATION
# Save weekly report as JSON + Markdown → sync to Obsidian vault
# ══════════════════════════════════════════════════════════════════════════════

def phase_5_report(intel: dict, content: dict, revenue: dict, opt: dict) -> Path:
    phase_header(5, "REPORT GENERATION")

    week   = week_id()
    report = {
        "schema_version": SCHEMA_VERSION,
        "week":           week,
        "generated_at":   datetime.now().isoformat(),
        "next_run":       next_monday().isoformat(),
        "intelligence":   intel,
        "content_queue":  content,
        "revenue":        revenue,
        "optimisation":   opt,
    }

    # Save JSON
    json_path = WEEKLY_REPORTS / f"{week}.json"
    save_json(report, json_path)

    # Save Markdown
    md_path  = WEEKLY_REPORTS / f"{week}.md"
    _write_markdown(report, md_path)

    # Sync to Obsidian vault
    obsidian_log = OBSIDIAN / "04-Weekly-Logs" / f"{week}.md"
    if OBSIDIAN.exists():
        obsidian_log.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(md_path, obsidian_log)
        log.info(f"  Obsidian sync:  {obsidian_log}")

    log.info(f"  JSON report:    {json_path}")
    log.info(f"  Markdown:       {md_path}")
    return md_path


def _write_markdown(report: dict, path: Path):
    week    = report["week"]
    intel   = report["intelligence"]
    content = report["content_queue"]
    revenue = report["revenue"]
    opt     = report["optimisation"]
    nsfas   = intel.get("nsfas", {})
    moats   = opt.get("moat_scores", {})

    def bar(score, total=10):
        return "█" * score + "░" * (total - score)

    urgent_tasks   = content.get("urgent", [])
    weekly_tasks   = content.get("this_week", [])
    opportunities  = intel.get("opportunities", [])
    optimisations  = opt.get("optimisations", [])

    md = f"""---
week: {week}
date: {date.today().isoformat()}
type: weekly-intelligence-report
schema: {SCHEMA_VERSION}
tags: [enil, intelligence, weekly, {date.today().year}]
---

# ENIL Weekly Intelligence Report — {week}

> *"Every NSFAS crisis is a content event. Every DBE delay is a search spike.
> Every chaos event is a subscriber acquisition moment."*

---

## 📡 Intelligence Summary

| Source | Status | Signal |
|--------|--------|--------|
| NSFAS Portal | {'🟢 UP' if nsfas.get('portal_up') else '🔴 DOWN'} | {'Crisis ACTIVE' if nsfas.get('critical_active') else 'Stable'} |
| NSFAS State | {str(nsfas.get('current_state','')).replace('_',' ').title()} | {nsfas.get('new_alerts_7d',0)} new alerts (7d) |
| DBE | {'⚠️ MATRIC SEASON' if intel.get('dbe',{}).get('matric_season') else 'Normal'} | {intel.get('dbe',{}).get('new_docs_7d',0)} new docs |
| APS Database | {intel.get('aps',{}).get('total_programmes',0)} programmes | Age: {intel.get('aps',{}).get('data_age_days',0)}d |
| Labour Market | {intel.get('labour',{}).get('total_occupations',0)} occupations | {intel.get('labour',{}).get('critical_shortages',0)} critical shortages |

---

## 🔥 Antifragile Opportunities

"""
    if opportunities:
        for opp in opportunities:
            sev_icon = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(opp.get("severity",""), "⚪")
            md += f"### {sev_icon} {opp['type']}\n"
            md += f"- **Talebian value:** {opp.get('talebian_value','')}\n"
            md += f"- **Content action:** {opp.get('content_action','')}\n"
            md += f"- **SEO action:** {opp.get('seo_action','')}\n"
            md += f"- **Newsletter:** {opp.get('newsletter_action','')}\n"
            md += f"- **Effort:** {opp.get('effort_hours',0)}h\n\n"
    else:
        md += "_No critical opportunities this week — execute standard sprint rotation._\n\n"

    md += "---\n\n## 📋 Content Queue\n\n"

    if urgent_tasks:
        md += "### 🔴 Urgent\n"
        for t in urgent_tasks:
            md += f"- [ ] **{t['task'][:80]}** ({t['effort_h']}h) — `{', '.join(t.get('platform',[]))}`\n"
            if t.get("seo_note"):
                md += f"  - SEO: {t['seo_note']}\n"
        md += "\n"

    md += "### 📅 This Week\n"
    for t in sorted(weekly_tasks, key=lambda x: x.get("priority",9)):
        md += f"- [ ] **{t['task'][:80]}** ({t['effort_h']}h)\n"
        if t.get("details"):
            md += f"  - {t['details'][:120]}\n"
    md += f"\n**Total effort: {content.get('total_effort_h',0)}h**\n\n"

    md += f"""---

## 💰 Revenue Pipeline

| Metric | Value |
|--------|-------|
| Year target | R{revenue.get('year_target_r',0):,} |
| Won to date | R{revenue.get('won_r',0):,} ({revenue.get('pct_to_target',0)}%) |
| Open pipeline | R{revenue.get('pipeline_r',0):,} |
| Overdue follow-ups | {revenue.get('overdue_count',0)} |
| Total prospects | {revenue.get('total_prospects',0)} |

### Pipeline by Stage\n
"""
    for stage, count in revenue.get("by_stage", {}).items():
        md += f"- **{stage.replace('_',' ').title()}:** {count}\n"

    md += f"""
---

## 🏰 Moat Assessment

| Moat | Score | Bar |
|------|-------|-----|
"""
    for name, score in moats.items():
        md += f"| {name} | {score}/10 | `{bar(score)}` |\n"

    md += f"""
- **Antifragility Score:** {opt.get('antifragility',0)}/10

---

## ⚙️ System Optimisation

### Data Freshness\n
"""
    for src, age in opt.get("data_freshness",{}).items():
        icon = "✅" if age <= DATA_STALE_WARN else "⚠️" if age <= DATA_STALE_CRIT else "🔴"
        md += f"- {icon} `{src}`: {age} days old\n"

    md += "\n### Actions Required\n"
    if optimisations:
        for o in optimisations:
            md += f"- [{o['severity']}] **{o['type']}** — `{o['action']}`\n"
    else:
        md += "- ✅ All systems nominal\n"

    md += f"""
### GitHub Actions (verify manually)
- [data_monitor.yml]({opt.get('github_actions',{}).get('data_monitor_url','')})
- [site_rebuild.yml]({opt.get('github_actions',{}).get('site_rebuild_url','')})

---

*Next run: {report['next_run']} | Generated: {report['generated_at'][:16]} | Schema: {SCHEMA_VERSION}*
"""
    path.write_text(md, encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ENIL Weekly Agentic Orchestration Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python weekly_orchestrator.py                   # full run
  python weekly_orchestrator.py --phase 1         # intelligence scan only
  python weekly_orchestrator.py --phase 3         # revenue review only
  python weekly_orchestrator.py --dry-run         # print only, no file writes
  python weekly_orchestrator.py --skip-pipeline   # skip pipeline re-run (use cached data)
        """,
    )
    parser.add_argument("--phase",          type=int, choices=[1,2,3,4,5],
                        help="Run a single phase only")
    parser.add_argument("--dry-run",        action="store_true",
                        help="Print results but do not write any files")
    parser.add_argument("--skip-pipeline",  action="store_true",
                        help="Skip the data pipeline run (use last cached data)")
    args = parser.parse_args()

    week  = week_id()
    start = time.time()

    sep("═")
    log.info(f"  ENIL WEEKLY ORCHESTRATION  —  {week}")
    log.info(f"  {datetime.now().strftime('%A %d %B %Y  %H:%M')} SAST")
    log.info(f"  Dry-run: {args.dry_run}  |  Skip pipeline: {args.skip_pipeline}")
    sep("═")

    # ── Optionally refresh data pipeline first ──
    if not args.skip_pipeline and not args.dry_run and not args.phase:
        log.info("\n► Refreshing data pipeline before weekly review...")
        pipeline_script = BASE / "pipeline" / "pipeline.py"
        if pipeline_script.exists():
            try:
                subprocess.run(
                    [sys.executable, str(pipeline_script), "--source", "all"],
                    check=True, timeout=600, capture_output=False,
                )
                log.info("  Pipeline refresh: ✅ complete")
            except subprocess.CalledProcessError as e:
                log.warning(f"  Pipeline refresh: ⚠️  non-zero exit ({e.returncode}) — using cached data")
            except subprocess.TimeoutExpired:
                log.warning("  Pipeline refresh: ⚠️  timed out — using cached data")
        else:
            log.warning("  pipeline.py not found — using cached data")

    # ── Phase execution ──
    intel   = {}
    content = {}
    revenue = {}
    opt     = {}

    if not args.phase or args.phase == 1:
        intel = phase_1_intelligence_scan()
    if not args.phase or args.phase == 2:
        content = phase_2_content_queue(intel)
    if not args.phase or args.phase == 3:
        revenue = phase_3_revenue_pipeline()
    if not args.phase or args.phase == 4:
        opt = phase_4_optimisation()
    if not args.phase or args.phase == 5:
        if not args.dry_run:
            report_path = phase_5_report(intel, content, revenue, opt)
        else:
            log.info("\n  [DRY RUN] Report generation skipped")
            report_path = None

    # ── Final summary ──
    elapsed = round(time.time() - start, 1)
    sep("═")
    log.info(f"  ORCHESTRATION COMPLETE — {elapsed}s")
    log.info(f"  Opportunities found:  {len(intel.get('opportunities', []))}")
    log.info(f"  Content tasks queued: {len(content.get('this_week', [])) + len(content.get('urgent', []))}")
    log.info(f"  Revenue overdue:      {revenue.get('overdue_count', 0)} follow-ups")
    log.info(f"  Optimisations needed: {len(opt.get('optimisations', []))}")
    if report_path:
        log.info(f"  Report:               {report_path}")
    log.info(f"  Next run:             {next_monday().strftime('%A %d %B %Y')}")
    sep("═")
    log.info("")


if __name__ == "__main__":
    main()
