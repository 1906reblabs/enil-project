"""
===============================================================================
ENIL Build Manifest Generator
===============================================================================

Pipeline Version: 2.0.0

Responsibilities
----------------
• Generate site/build-manifest.json
• Record build metadata
• Capture Git information
• Record generated outputs
• Record changed sources
• Support cache invalidation
"""

from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("ENIL.manifest")

ROOT = Path(__file__).resolve().parents[2]

SITE = ROOT / "site"

MANIFEST = SITE / "build-manifest.json"

PIPELINE_VERSION = "2.0.0"


# =============================================================================
# Utilities
# =============================================================================

def _git(command: list[str]) -> str:

    try:
        return subprocess.check_output(
            command,
            cwd=ROOT,
            text=True,
        ).strip()

    except Exception:
        return "unknown"


def _git_sha():

    return _git(["git", "rev-parse", "HEAD"])


def _git_short_sha():

    return _git(["git", "rev-parse", "--short", "HEAD"])


def _git_branch():

    return _git(["git", "rev-parse", "--abbrev-ref", "HEAD"])


# =============================================================================
# Generator
# =============================================================================

class ManifestGenerator:

    def __init__(self):

        self.manifest = {}

    # -------------------------------------------------------------------------

    def build(

        self,

        pipeline_summary: dict[str, Any],

        json_result=None,

        html_result=None,

    ):

        now = datetime.now(timezone.utc)

        self.manifest = {

            "manifest_version": 1,

            "pipeline_version": PIPELINE_VERSION,

            "generated_at": now.isoformat(),

            "build_id": os.environ.get(
                "GITHUB_RUN_ID",
                "local",
            ),

            "build_number": os.environ.get(
                "GITHUB_RUN_NUMBER",
                "local",
            ),

            "workflow": os.environ.get(
                "GITHUB_WORKFLOW",
                "manual",
            ),

            "trigger": os.environ.get(
                "GITHUB_EVENT_NAME",
                "manual",
            ),

            "repository": os.environ.get(
                "GITHUB_REPOSITORY",
                "local",
            ),

            "branch": _git_branch(),

            "commit": {

                "sha": _git_sha(),

                "short_sha": _git_short_sha(),

            },

            "environment": {

                "python": platform.python_version(),

                "platform": platform.platform(),

                "github_actions": bool(
                    os.environ.get(
                        "GITHUB_ACTIONS"
                    )
                ),

            },

            "pipeline": pipeline_summary,

            "json": self._json_summary(json_result),

            "html": self._html_summary(html_result),

        }

        return self

    # -------------------------------------------------------------------------

    def _json_summary(self, result):

        if result is None:

            return {}

        return {

            "changed": result.changed,

            "generated_files": result.generated_files,

            "records": result.records,

        }

    # -------------------------------------------------------------------------

    def _html_summary(self, result):

        if result is None:

            return {}

        return {

            "changed": result.changed,

            "pages": result.generated_pages,

            "assets": result.copied_assets,

        }

    # -------------------------------------------------------------------------

    def write(self):

        SITE.mkdir(parents=True, exist_ok=True)

        with open(

            MANIFEST,

            "w",

            encoding="utf-8",

        ) as f:

            json.dump(

                self.manifest,

                f,

                indent=2,

                ensure_ascii=False,

            )

        log.info(

            "Build manifest written: %s",

            MANIFEST,

        )

        return MANIFEST


# =============================================================================
# Public API
# =============================================================================

def generate_manifest(

    pipeline_summary,

    json_result=None,

    html_result=None,

):

    generator = ManifestGenerator()

    generator.build(

        pipeline_summary,

        json_result,

        html_result,

    )

    return generator.write()
