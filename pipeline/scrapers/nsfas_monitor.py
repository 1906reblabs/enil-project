#!/usr/bin/env python3
"""
ENIL NSFAS Monitor  v1.0.0
===========================
Talebian core: every NSFAS crisis is a CONTENT EVENT.
Every portal crash is a search spike. Every new circular = new subscriber.

Monitors:
  https://mynsfas.nsfas.org.za           (portal status)
  https://www.nsfas.org.za/content/circular-letters.html
  https://www.nsfas.org.za/content/apply.html
"""

import hashlib, json, logging, uuid
from datetime import datetime, date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("ENIL.nsfas")

HEADERS       = {"User-Agent": "ENIL-Navigator/1.0 (research; contact@enil.co.za)"}
NSFAS_BASE    = "https://www.nsfas.org.za"
MYNSFAS_URL   = "https://mynsfas.nsfas.org.za"
CIRCULARS_URL = f"{NSFAS_BASE}/content/circular-letters.html"

# ─── Full state machine definition ───────────────────────────────────────────

STATES = {
    "pre_application": {
        "label":   "STATE 0 — Pre-Application",
        "period":  "October–November (Grade 12 year)",
        "desc":    "myNSFAS portal opens. Deadline-critical window.",
        "docs_required": [
            "Certified ID (≤3 months old)",
            "Proof of income (SASSA / payslips / affidavit)",
            "Institutional application confirmation",
        ],
        "action": "Submit on mynsfas.nsfas.org.za before closing date",
        "templates": ["application_checklist.pdf","income_proof_guide.pdf"],
        "crisis_types": ["portal_down","deadline_extended","income_threshold_changed"],
    },
    "submitted_pending": {
        "label":   "STATE 1 — Submitted / Pending",
        "period":  "November–January",
        "desc":    "Awaiting processing. Portal crashes during peak volume.",
        "docs_required": ["Screenshot of submission confirmation","Reference number"],
        "action": "Save confirmation screenshot. Monitor portal weekly.",
        "templates": ["alternative_submission_evidence.pdf"],
        "crisis_types": ["portal_crash","duplicate_applications","reference_invalid"],
    },
    "provisionally_funded": {
        "label":   "STATE 2 — Provisionally Funded",
        "period":  "January–February",
        "desc":    "Conditional approval. Conditions often NOT clearly communicated.",
        "docs_required": ["Proof of registration","Academic record (if returning student)"],
        "action": "Check all conditions. Submit outstanding docs immediately.",
        "templates": ["condition_checklist_by_institution.pdf"],
        "crisis_types": ["conditions_unclear","registration_proof_format_rejected"],
    },
    "appeals_window": {
        "label":   "STATE 3 — Appeals Window  ← MOST CRITICAL",
        "period":  "March–May",
        "desc":    "Appeal against rejection. ~43% success rate when correct grounds cited.",
        "docs_required": [
            "Rejection letter with rejection code",
            "Supporting docs per code",
            "Completed appeal template",
        ],
        "action": "Identify rejection code → match appeal grounds → submit within 30 days.",
        "templates": [
            "appeals_letter_template.docx",
            "rejection_code_lookup.pdf",
            "supporting_docs_by_code.pdf",
        ],
        "crisis_types": [
            "wrong_rejection_code","appeal_portal_broken",
            "turnaround_exceeded_30_days","appeal_rejected_without_reason",
        ],
        "rejection_codes": {
            "R01": {"reason":"Income exceeds threshold",       "action":"Submit updated income proof; request re-assessment"},
            "R02": {"reason":"Not SA citizen/PR",              "action":"Submit certified ID + birth certificate"},
            "R03": {"reason":"Other bursary received",         "action":"Submit letter confirming partial coverage only"},
            "R04": {"reason":"Academic record insufficient",   "action":"Submit certified transcript + compassionate grounds letter"},
            "R05": {"reason":"Programme not NSFAS-funded",     "action":"Check DHET list; ask institution to re-register programme"},
            "R06": {"reason":"Duplicate application",          "action":"Request confirmation of active application; deactivate duplicate"},
            "R07": {"reason":"Income not verified",            "action":"Submit SARS ITR or SASSA verification; request manual review"},
        },
    },
    "disbursement_active": {
        "label":   "STATE 4 — Disbursement Active",
        "period":  "February–November",
        "desc":    "Funds flowing. Allowance and tuition disputes have DIFFERENT paths.",
        "docs_required": ["Bank statement","Accommodation lease (if applicable)"],
        "action": "Track schedule. Report discrepancies within 5 business days.",
        "templates": ["allowance_dispute_path.pdf","tuition_dispute_path.pdf"],
        "crisis_types": [
            "allowance_not_deposited","wrong_allowance_amount",
            "tuition_not_paid","accommodation_allowance_rejected",
        ],
        "resolution_paths": {
            "allowance": "Call 0800 067 327 → wait 7 days → escalate to institution",
            "tuition":   "Contact institution financial aid office → institution contacts NSFAS",
        },
    },
    "continuation": {
        "label":   "STATE 5 — Continuation (Year 2+)",
        "period":  "September–October",
        "desc":    "Reapplication. Academic progress thresholds apply.",
        "docs_required": ["Transcript showing pass requirements","Continuing registration proof"],
        "action": "Check institution-specific thresholds. Reapply before deadline.",
        "templates": ["continuation_requirements_by_institution.pdf"],
        "crisis_types": [
            "pass_threshold_changed","supplementary_results_not_updated",
            "deregistered_despite_passing",
        ],
        "thresholds": {
            "university": "Pass ≥50% of registered modules per year",
            "tvet":       "Pass ≥60% of subjects per level",
        },
    },
}


class NSFASMonitor:
    def __init__(self, output_dir: Path):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def run(self) -> dict:
        results = {"alerts": 0, "state_updates": 0,
                   "new_circulars": 0, "portal_status": "unknown"}

        # 1. Portal health check
        up = self._check_portal()
        results["portal_status"] = "up" if up else "down"
        if not up:
            self._emit_alert(
                state="submitted_pending",
                title="⚠️ myNSFAS Portal Down / Unreachable",
                body=("The myNSFAS portal is currently returning errors. "
                      "Do NOT re-submit your application — this creates duplicate records. "
                      "Screenshot your existing reference number. Try again after 18:00 "
                      "or use the NSFAS mobile app."),
                severity="critical",
                action="Screenshot your reference. Call 0800 067 327 if urgent.",
            )
            results["alerts"] += 1

        # 2. New circulars
        new = self._check_circulars()
        results["new_circulars"] = len(new)
        results["alerts"] += len(new)

        # 3. Save full state machine
        self._save_state_machine()
        results["state_updates"] = len(STATES)

        # 4. Current state
        cur = self._current_state()
        self._save_json({"current_state": cur, "state_data": STATES[cur],
                         "determined_at": datetime.now().isoformat()},
                        "current_state.json")
        return results

    def _check_portal(self) -> bool:
        try:
            r = self.session.get(MYNSFAS_URL, timeout=15)
            return r.status_code == 200
        except Exception:
            return False

    def _check_circulars(self) -> list:
        mf = self.out / "circular_manifest.json"
        manifest = json.load(open(mf)) if mf.exists() else {"circulars": []}
        known = {c["hash"] for c in manifest["circulars"]}
        new = []
        try:
            r = self.session.get(CIRCULARS_URL, timeout=30)
            if r.status_code != 200: return []
            h = hashlib.md5(r.text.encode()).hexdigest()
            if h not in known:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    if a["href"].endswith(".pdf"):
                        rec = {"url": f"{NSFAS_BASE}{a['href']}",
                               "title": a.get_text(strip=True),
                               "hash": h, "found": date.today().isoformat()}
                        new.append(rec)
                        manifest["circulars"].append(rec)
                        self._emit_alert(
                            state="pre_application",
                            title=f"📄 New NSFAS Circular: {a.get_text(strip=True)[:50]}",
                            body=f"New circular published. Review for deadline/requirement changes: {rec['url']}",
                            severity="warning",
                            action="Read circular and update your checklist.",
                        )
        except Exception as e:
            log.warning(f"  Circulars check failed: {e}")
        with open(mf, "w") as f:
            json.dump(manifest, f, indent=2)
        return new

    def _current_state(self) -> str:
        m = datetime.now().month
        if m in (10, 11): return "pre_application"
        if m in (12, 1):  return "submitted_pending"
        if m == 2:        return "provisionally_funded"
        if m in (3,4,5):  return "appeals_window"
        if m == 9:        return "continuation"
        return "disbursement_active"

    def _emit_alert(self, state, title, body, severity, action):
        af = self.out / "alerts.json"
        alerts = json.load(open(af)) if af.exists() else []
        alerts.append({
            "alert_id": str(uuid.uuid4())[:8],
            "state": state, "title": title, "body": body,
            "severity": severity, "action_required": action,
            "published_at": datetime.now().isoformat(),
        })
        with open(af, "w") as f:
            json.dump(alerts, f, indent=2, default=str)

    def _save_state_machine(self):
        self._save_json(
            {"version":"1.0.0","updated":datetime.now().isoformat(),"states":STATES},
            "state_machine.json"
        )

    def _save_json(self, data, filename):
        with open(self.out / filename, "w") as f:
            json.dump(data, f, indent=2, default=str)
        log.info(f"  Saved {filename}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    r = NSFASMonitor(Path("./data/nsfas")).run()
    print(f"Results: {r}")
