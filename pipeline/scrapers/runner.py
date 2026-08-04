"""
===============================================================================
ENIL Scraper Runner
===============================================================================

Pipeline Version: 2.0.0

Responsibilities
----------------
• Execute any configured scraper
• Measure execution time
• Capture exceptions
• Standardize results
• Detect changed files
• Support incremental builds
• Produce metrics for build summary

This module is intentionally generic. It knows nothing about NSFAS,
DBE, APS or Labour.
"""

from __future__ import annotations

import hashlib
import logging
import time
import traceback
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from config import SourceConfig, load_scraper

log = logging.getLogger("ENIL.runner")


# =============================================================================
# Result object
# =============================================================================

@dataclass
class RunnerResult:

    source: str

    status: str

    duration_seconds: float

    records: int = 0

    changed: bool = False

    output_directory: str = ""

    warnings: list[str] | None = None

    errors: list[str] | None = None

    metadata: dict[str, Any] | None = None

    def to_dict(self):

        return asdict(self)


# =============================================================================
# Utility
# =============================================================================

def directory_checksum(directory: Path):

    """
    Compute a checksum for all files in a directory.

    Used to detect incremental changes.
    """

    if not directory.exists():

        return ""

    digest = hashlib.sha256()

    files = sorted(directory.rglob("*"))

    for path in files:

        if not path.is_file():
            continue

        digest.update(path.name.encode())

        digest.update(path.read_bytes())

    return digest.hexdigest()


# =============================================================================
# Runner
# =============================================================================

class ScraperRunner:

    def __init__(self):

        pass

    # -------------------------------------------------------------------------

    def run(self, source: SourceConfig):

        output_dir = Path(source.output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        before = directory_checksum(output_dir)

        started = time.perf_counter()

        warnings = []

        errors = []

        metadata = {}

        records = 0

        try:

            scraper_class = load_scraper(source)

            scraper = scraper_class(output_dir)

            result = scraper.run()

            if isinstance(result, dict):

                records = result.get("records", 0)

                metadata = result

            elif result is None:

                metadata = {}

            else:

                metadata = {
                    "result": result
                }

            status = "success"

        except Exception as ex:

            status = "failed"

            errors.append(str(ex))

            errors.append(traceback.format_exc())

            log.exception(
                "Scraper '%s' failed.",
                source.name,
            )

        duration = round(

            time.perf_counter() - started,

            2,

        )

        after = directory_checksum(output_dir)

        changed = before != after

        return RunnerResult(

            source=source.name,

            status=status,

            duration_seconds=duration,

            records=records,

            changed=changed,

            output_directory=str(output_dir),

            warnings=warnings,

            errors=errors,

            metadata=metadata,

        )


# =============================================================================
# Batch Runner
# =============================================================================

class PipelineRunner:

    """
    Executes all configured sources.
    """

    def __init__(self):

        self.runner = ScraperRunner()

    # -------------------------------------------------------------------------

    def execute(self, sources):

        results = []

        for source in sources:

            log.info(

                "Running %s...",

                source.name,

            )

            results.append(

                self.runner.run(source)

            )

        return results


# =============================================================================
# Metrics
# =============================================================================

def summarize(results):

    summary = {

        "sources": len(results),

        "successful": 0,

        "failed": 0,

        "changed_sources": [],

        "records": 0,

        "duration_seconds": 0,

    }

    for r in results:

        summary["duration_seconds"] += r.duration_seconds

        summary["records"] += r.records

        if r.status == "success":

            summary["successful"] += 1

        else:

            summary["failed"] += 1

        if r.changed:

            summary["changed_sources"].append(

                r.source

            )

    summary["duration_seconds"] = round(

        summary["duration_seconds"],

        2,

    )

    return summary
