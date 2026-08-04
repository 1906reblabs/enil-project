"""
===============================================================================
ENIL JSON Generator
===============================================================================

Pipeline Version: 2.0.0

Responsibilities
----------------
• Generate website JSON data
• Copy validated datasets into site/data
• Produce search index
• Produce latest.json
• Produce build metadata
• Support incremental generation

Author: ENIL
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("ENIL.json_generator")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

PIPELINE_DATA = ROOT / "pipeline" / "data"

SITE_DATA = ROOT / "site" / "data"

SITE_DATA.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def write_json(path: Path, obj: Any):

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:

        json.dump(

            obj,

            f,

            indent=2,

            ensure_ascii=False,

        )


def checksum(path: Path):

    if not path.exists():

        return ""

    return hashlib.sha256(

        path.read_bytes()

    ).hexdigest()


# -----------------------------------------------------------------------------
# Generator
# -----------------------------------------------------------------------------

@dataclass
class JSONGenerationResult:

    generated_files: list[str]

    skipped_files: list[str]

    records: int

    changed: bool


class JSONGenerator:

    def __init__(self):

        self.generated = []

        self.skipped = []

        self.records = 0

        self.changed = False

    # -------------------------------------------------------------------------

    def generate(self):

        log.info("Generating website JSON...")

        self.copy_nsfas()

        self.copy_labour()

        self.generate_aps()

        self.generate_latest()

        self.generate_search()

        self.generate_metadata()

        return JSONGenerationResult(

            generated_files=self.generated,

            skipped_files=self.skipped,

            records=self.records,

            changed=self.changed,

        )

    # -------------------------------------------------------------------------

    def _copy_json(self, source: Path, destination: str):

        target = SITE_DATA / destination

        if not source.exists():

            return

        before = checksum(target)

        shutil.copy2(source, target)

        after = checksum(target)

        self.generated.append(destination)

        if before != after:

            self.changed = True

    # -------------------------------------------------------------------------

    def copy_nsfas(self):

        self._copy_json(

            PIPELINE_DATA / "nsfas" / "alerts.json",

            "nsfas_alerts.json",

        )

    # -------------------------------------------------------------------------

    def copy_labour(self):

        self._copy_json(

            PIPELINE_DATA / "labour" / "demand_gap.json",

            "demand_gap.json",

        )

    # -------------------------------------------------------------------------

    def generate_aps(self):

        csv_file = (

            PIPELINE_DATA /

            "aps" /

            "aps_requirements.csv"

        )

        if not csv_file.exists():

            return

        programmes = []

        with open(

            csv_file,

            newline="",

            encoding="utf-8",

        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                programmes.append(row)

        self.records += len(programmes)

        output = {

            "generated":

                datetime.utcnow().isoformat() + "Z",

            "count":

                len(programmes),

            "programmes":

                programmes,

        }

        write_json(

            SITE_DATA /

            "aps_programmes.json",

            output,

        )

        self.generated.append(

            "aps_programmes.json"

        )

        self.changed = True

    # -------------------------------------------------------------------------

    def generate_latest(self):

        latest = {

            "generated":

                datetime.utcnow().isoformat() + "Z",

            "datasets": [

                x.name

                for x in PIPELINE_DATA.iterdir()

                if x.is_dir()

            ]

        }

        write_json(

            SITE_DATA /

            "latest.json",

            latest,

        )

        self.generated.append(

            "latest.json"

        )

    # -------------------------------------------------------------------------

    def generate_search(self):

        search = []

        alerts = (

            PIPELINE_DATA /

            "nsfas" /

            "alerts.json"

        )

        if alerts.exists():

            with open(

                alerts,

                encoding="utf-8",

            ) as f:

                data = json.load(f)

                for item in data:

                    search.append({

                        "title":

                            item.get("title"),

                        "category":

                            "NSFAS",

                        "url":

                            "/nsfas/",

                    })

        write_json(

            SITE_DATA /

            "search.json",

            search,

        )

        self.generated.append(

            "search.json"

        )

    # -------------------------------------------------------------------------

    def generate_metadata(self):

        metadata = {

            "generated":

                datetime.utcnow().isoformat() + "Z",

            "generated_files":

                self.generated,

            "records":

                self.records,

            "pipeline":

                "2.0.0",

        }

        write_json(

            SITE_DATA /

            "metadata.json",

            metadata,

        )

        self.generated.append(

            "metadata.json"

        )


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def generate_json():

    return JSONGenerator().generate()
