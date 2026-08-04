"""
===============================================================================
ENIL HTML Generator
===============================================================================

Pipeline Version: 2.0.0

Responsibilities
----------------
• Generate HTML pages using Jinja2 templates
• Support incremental page generation
• Generate index and section pages
• Copy static assets
• Produce sitemap metadata

Directory Layout
----------------

templates/
    layout.html
    index.html
    category.html
    article.html

site/
    index.html
    nsfas/index.html
    aps/index.html
    labour/index.html
    dbe/index.html
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape

log = logging.getLogger("ENIL.html")


ROOT = Path(__file__).resolve().parents[2]

SITE = ROOT / "site"

DATA = SITE / "data"

TEMPLATES = ROOT / "templates"

STATIC = ROOT / "static"

env = Environment(
    loader=FileSystemLoader(TEMPLATES),
    autoescape=select_autoescape(["html", "xml"]),
)

env.globals["build_time"] = datetime.utcnow


# =============================================================================
# Result
# =============================================================================

@dataclass
class HTMLResult:

    generated_pages: list[str]

    copied_assets: int

    changed: bool


# =============================================================================
# Generator
# =============================================================================

class HTMLGenerator:

    def __init__(self):

        self.generated = []

        self.assets = 0

        self.changed = False

    # -------------------------------------------------------------------------

    def generate(self):

        log.info("Generating HTML...")

        self.copy_assets()

        self.build_home()

        self.build_nsfas()

        self.build_aps()

        self.build_labour()

        self.build_dbe()

        self.build_404()

        return HTMLResult(

            generated_pages=self.generated,

            copied_assets=self.assets,

            changed=self.changed,

        )

    # -------------------------------------------------------------------------

    def render(self, template_name, destination, **context):

        template = env.get_template(template_name)

        html = template.render(**context)

        destination.parent.mkdir(parents=True, exist_ok=True)

        existing = ""

        if destination.exists():
            existing = destination.read_text(encoding="utf-8")

        if existing != html:

            destination.write_text(

                html,

                encoding="utf-8",

            )

            self.changed = True

        self.generated.append(

            str(destination.relative_to(SITE))

        )

    # -------------------------------------------------------------------------

    def load_json(self, filename):

        file = DATA / filename

        if not file.exists():

            return {}

        with open(file, encoding="utf-8") as f:

            return json.load(f)

    # -------------------------------------------------------------------------

    def build_home(self):

        self.render(

            "index.html",

            SITE / "index.html",

            latest=self.load_json("latest.json"),

            metadata=self.load_json("metadata.json"),

        )

    # -------------------------------------------------------------------------

    def build_nsfas(self):

        self.render(

            "category.html",

            SITE / "nsfas" / "index.html",

            title="NSFAS",

            alerts=self.load_json("nsfas_alerts.json"),

        )

    # -------------------------------------------------------------------------

    def build_aps(self):

        self.render(

            "category.html",

            SITE / "aps" / "index.html",

            title="APS Calculator",

            programmes=self.load_json("aps_programmes.json"),

        )

    # -------------------------------------------------------------------------

    def build_labour(self):

        self.render(

            "category.html",

            SITE / "labour" / "index.html",

            title="Labour",

            demand=self.load_json("demand_gap.json"),

        )

    # -------------------------------------------------------------------------

    def build_dbe(self):

        self.render(

            "category.html",

            SITE / "dbe" / "index.html",

            title="Department of Basic Education",

        )

    # -------------------------------------------------------------------------

    def build_404(self):

        self.render(

            "404.html",

            SITE / "404.html",

        )

    # -------------------------------------------------------------------------

    def copy_assets(self):

        if not STATIC.exists():

            return

        target = SITE / "assets"

        target.mkdir(parents=True, exist_ok=True)

        for file in STATIC.rglob("*"):

            if file.is_file():

                rel = file.relative_to(STATIC)

                destination = target / rel

                destination.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(file, destination)

                self.assets += 1


# =============================================================================
# Public API
# =============================================================================

def generate_html():

    generator = HTMLGenerator()

    return generator.generate()
