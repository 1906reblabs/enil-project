"""
===============================================================================
ENIL Build Summary
===============================================================================

Pipeline Version: 2.0.0

Responsibilities
----------------
• Produce machine-readable build summary (JSON)
• Produce GitHub Actions Markdown summary
• Write summary to GitHub Step Summary
• Save summary as an artifact
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

REPORTS_DIR = ROOT / "pipeline" / "reports" / "output"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

JSON_REPORT = REPORTS_DIR / "build_summary.json"
MARKDOWN_REPORT = REPORTS_DIR / "build_summary.md"


# =============================================================================
# Utilities
# =============================================================================

def _to_dict(obj: Any):

    if obj is None:
        return {}

    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, dict):
        return obj

    return vars(obj)


# =============================================================================
# Summary Builder
# =============================================================================

class BuildSummary:

    def __init__(
        self,
        pipeline_summary: dict,
        json_result=None,
        html_result=None,
        validation=None,
    ):

        self.pipeline = _to_dict(pipeline_summary)
        self.json = _to_dict(json_result)
        self.html = _to_dict(html_result)
        self.validation = _to_dict(validation)

    # -------------------------------------------------------------------------

    def build(self):

        return {

            "generated_at":
                datetime.now(timezone.utc).isoformat(),

            "pipeline":
                self.pipeline,

            "json":
                self.json,

            "html":
                self.html,

            "validation":
                self.validation,

        }

    # -------------------------------------------------------------------------

    def save_json(self):

        report = self.build()

        with open(
            JSON_REPORT,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                report,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return JSON_REPORT

    # -------------------------------------------------------------------------

    def markdown(self):

        p = self.pipeline

        j = self.json

        h = self.html

        lines = []

        lines.append("# ENIL Build Summary")
        lines.append("")
        lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        lines.append("## Pipeline")
        lines.append("")
        lines.append(f"- Sources: {p.get('sources',0)}")
        lines.append(f"- Successful: {p.get('successful',0)}")
        lines.append(f"- Failed: {p.get('failed',0)}")
        lines.append(f"- Records: {p.get('records',0)}")
        lines.append(f"- Duration: {p.get('duration_seconds',0)} sec")
        lines.append("")

        changed = p.get("changed_sources", [])

        if changed:
            lines.append("### Changed Sources")
            lines.append("")
            for src in changed:
                lines.append(f"- {src}")
            lines.append("")

        lines.append("## JSON Generation")
        lines.append("")
        lines.append(
            f"- Files Generated: {len(j.get('generated_files',[]))}"
        )
        lines.append(
            f"- Records: {j.get('records',0)}"
        )
        lines.append(
            f"- Changed: {j.get('changed',False)}"
        )
        lines.append("")

        lines.append("## HTML Generation")
        lines.append("")
        lines.append(
            f"- Pages Generated: {len(h.get('generated_pages',[]))}"
        )
        lines.append(
            f"- Assets Copied: {h.get('copied_assets',0)}"
        )
        lines.append(
            f"- Changed: {h.get('changed',False)}"
        )
        lines.append("")

        if self.validation:

            lines.append("## Validation")
            lines.append("")

            if self.validation.get("passed", True):

                lines.append("✅ Validation Passed")

            else:

                lines.append("❌ Validation Failed")

            warnings = self.validation.get("warnings", [])

            if warnings:

                lines.append("")
                lines.append("### Warnings")

                for warning in warnings:
                    lines.append(f"- {warning}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------

    def save_markdown(self):

        md = self.markdown()

        MARKDOWN_REPORT.write_text(
            md,
            encoding="utf-8",
        )

        return MARKDOWN_REPORT

    # -------------------------------------------------------------------------

    def publish_to_github(self):

        summary = os.environ.get("GITHUB_STEP_SUMMARY")

        if not summary:

            return

        with open(
            summary,
            "a",
            encoding="utf-8",
        ) as f:

            f.write(self.markdown())

            f.write("\n")

    # -------------------------------------------------------------------------

    def generate(self):

        self.save_json()

        self.save_markdown()

        self.publish_to_github()

        return {

            "json": str(JSON_REPORT),

            "markdown": str(MARKDOWN_REPORT),

        }


# =============================================================================
# Public API
# =============================================================================

def generate_build_summary(
    pipeline_summary,
    json_result=None,
    html_result=None,
    validation=None,
):

    summary = BuildSummary(
        pipeline_summary,
        json_result,
        html_result,
        validation,
    )

    return summary.generate()
