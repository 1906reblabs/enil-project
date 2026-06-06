#!/usr/bin/env python3
"""
ENIL Data Pipeline — Main Orchestrator  v1.0.0
================================================
Extract → Classify → Validate → Store → Publish

Usage:
  python pipeline.py                   # full run
  python pipeline.py --source nsfas    # single source
  python pipeline.py --dry-run         # validate only, no writes
  python pipeline.py --force-rebuild   # rebuild all site output

Sources: dbe | nsfas | aps | labour | all (default)

Scheduled: .github/workflows/data_monitor.yml  (daily 06:00 SAST)
"""

import argparse, json, logging, os, sys, time, uuid
from datetime import datetime, date
from pathlib import Path

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("enil_pipeline.log", mode="a"),
    ],
)
log = logging.getLogger("ENIL.pipeline")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RUNS_DIR = BASE_DIR / "runs"
DATA_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True)


# ─── Source runners ───────────────────────────────────────────────────────────

def run_dbe():
    from scrapers.dbe_scraper import DBEScraper
    return DBEScraper(DATA_DIR / "dbe").run()

def run_nsfas():
    from scrapers.nsfas_monitor import NSFASMonitor
    return NSFASMonitor(DATA_DIR / "nsfas").run()

def run_aps():
    from scrapers.aps_scraper import APSScraper
    return APSScraper(DATA_DIR / "aps").run()

def run_labour():
    from scrapers.labour_scraper import LabourScraper
    return LabourScraper(DATA_DIR / "labour").run()


SOURCE_MAP = {"dbe": run_dbe, "nsfas": run_nsfas, "aps": run_aps, "labour": run_labour}


# ─── Schema validation ────────────────────────────────────────────────────────

def validate_all() -> tuple[bool, list[str]]:
    import csv
    from schema import NSFASAlert

    errors = []
    ok     = 0

    aps_csv = DATA_DIR / "aps" / "aps_requirements.csv"
    if aps_csv.exists():
        with open(aps_csv) as f:
            for i, row in enumerate(csv.DictReader(f)):
                for field in ("institution", "programme", "min_aps"):
                    if not row.get(field):
                        errors.append(f"APS row {i}: missing {field}")
                    else:
                        ok += 1

    alerts_json = DATA_DIR / "nsfas" / "alerts.json"
    if alerts_json.exists():
        with open(alerts_json) as f:
            for a in json.load(f):
                try:
                    NSFASAlert(**a); ok += 1
                except Exception as e:
                    errors.append(f"NSFAS alert: {e}")

    log.info(f"  Validation: {ok} OK | {len(errors)} errors")
    return len(errors) == 0, errors


# ─── Site publisher ───────────────────────────────────────────────────────────

def publish_site():
    log.info("► Publishing data to site...")
    site_data = BASE_DIR.parent / "enil-site" / "site" / "data"
    site_data.mkdir(parents=True, exist_ok=True)

    # Gap table → JSON
    gap = DATA_DIR / "labour" / "demand_gap.json"
    if gap.exists():
        import shutil; shutil.copy(gap, site_data / "demand_gap.json")

    # APS data → JSON (for calculator)
    aps_csv = DATA_DIR / "aps" / "aps_requirements.csv"
    if aps_csv.exists():
        import csv
        rows = []
        with open(aps_csv) as f:
            for r in csv.DictReader(f):
                rows.append(r)
        with open(site_data / "aps_programmes.json", "w") as f:
            json.dump({"programmes": rows, "updated": date.today().isoformat()}, f, indent=2)

    # NSFAS alerts → JSON
    alerts = DATA_DIR / "nsfas" / "alerts.json"
    if alerts.exists():
        import shutil; shutil.copy(alerts, site_data / "nsfas_alerts.json")

    log.info("  Site data updated.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all",
                        choices=["all","dbe","nsfas","aps","labour"])
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--no-publish",   action="store_true")
    parser.add_argument("--force-rebuild",action="store_true")
    args = parser.parse_args()

    run_id = str(uuid.uuid4())[:8]
    start  = time.time()
    log.info(f"\n{'='*55}")
    log.info(f"ENIL Pipeline  RUN {run_id}  {datetime.now():%Y-%m-%d %H:%M} SAST")
    log.info(f"Source: {args.source}  |  Dry-run: {args.dry_run}")
    log.info(f"{'='*55}\n")

    results = {
        "run_id": run_id,
        "run_date": datetime.now().isoformat(),
        "triggered_by": "cron" if os.environ.get("GITHUB_ACTIONS") else "manual",
        "sources": {},
        "validation_passed": False,
        "validation_errors": [],
    }

    sources = list(SOURCE_MAP.keys()) if args.source == "all" else [args.source]

    for src in sources:
        log.info(f"► {src.upper()} pipeline...")
        try:
            results["sources"][src] = SOURCE_MAP[src]()
        except ImportError:
            log.warning(f"  Scraper '{src}' not yet installed — skipping")
            results["sources"][src] = {"status": "not_implemented"}
        except Exception as e:
            log.error(f"  Error in {src}: {e}")
            results["sources"][src] = {"status": "error", "error": str(e)}

    log.info("\n► Validating schema...")
    passed, errors = validate_all()
    results["validation_passed"] = passed
    results["validation_errors"] = errors

    if not args.dry_run and not args.no_publish and passed:
        publish_site()

    results["duration_seconds"] = round(time.time() - start, 2)
    if not args.dry_run:
        run_file = RUNS_DIR / f"run_{run_id}.json"
        with open(run_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

    log.info(f"\n{'='*55}")
    log.info(f"Done in {results['duration_seconds']}s  |  "
             f"{'✅ PASSED' if passed else '⚠️ FAILED'}")
    log.info(f"{'='*55}\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
