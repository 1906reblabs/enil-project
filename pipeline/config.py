"""
===============================================================================
ENIL Configuration Manager
===============================================================================

Loads and validates pipeline/config/sources.yaml

Responsibilities
----------------
• Load YAML configuration
• Validate required fields
• Return enabled sources
• Sort sources by priority
• Dynamically import scraper classes
• Provide build/publishing/logging configuration

Pipeline Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import yaml


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_FILE = CONFIG_DIR / "sources.yaml"


# -----------------------------------------------------------------------------
# Dataclasses
# -----------------------------------------------------------------------------

@dataclass
class SourceConfig:
    name: str
    enabled: bool
    priority: int
    module: str
    class_name: str
    output_dir: str
    publish_dir: str
    schedule: str
    description: str
    incremental: bool = True
    validate: bool = True
    publish: bool = True
    timeout_seconds: int = 600


# -----------------------------------------------------------------------------
# Configuration Manager
# -----------------------------------------------------------------------------

class ConfigManager:

    def __init__(self, config_path: Path | None = None):

        self.config_path = config_path or CONFIG_FILE

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.raw = yaml.safe_load(f)

        self.defaults = self.raw.get("defaults", {})

    # -------------------------------------------------------------------------

    def version(self):

        return self.raw.get("version", "unknown")

    # -------------------------------------------------------------------------

    def build(self):

        return self.raw.get("build", {})

    # -------------------------------------------------------------------------

    def publishing(self):

        return self.raw.get("publishing", {})

    # -------------------------------------------------------------------------

    def logging(self):

        return self.raw.get("logging", {})

    # -------------------------------------------------------------------------

    def get_source(self, name: str) -> SourceConfig:

        sources = self.raw.get("sources", {})

        if name not in sources:
            raise KeyError(f"Unknown source '{name}'")

        src = sources[name]

        module = src.get("module")
        class_name = src.get("class")

        if module is None or class_name is None:
            raise ValueError(
                f"{name}: both 'module' and 'class' must be specified."
            )

        return SourceConfig(

            name=name,

            enabled=src.get(
                "enabled",
                self.defaults.get("enabled", True),
            ),

            priority=src.get("priority", 999),

            module=module,

            class_name=class_name,

            output_dir=src["output_dir"],

            publish_dir=src["publish_dir"],

            schedule=src.get("schedule", "daily"),

            description=src.get("description", ""),

            incremental=src.get(
                "incremental",
                self.defaults.get("incremental", True),
            ),

            validate=src.get(
                "validate",
                self.defaults.get("validate", True),
            ),

            publish=src.get(
                "publish",
                self.defaults.get("publish", True),
            ),

            timeout_seconds=src.get(
                "timeout_seconds",
                self.defaults.get("timeout_seconds", 600),
            ),
        )

    # -------------------------------------------------------------------------

    def enabled_sources(self):

        result = []

        for name in self.raw.get("sources", {}):

            source = self.get_source(name)

            if source.enabled:
                result.append(source)

        result.sort(key=lambda s: s.priority)

        return result

    # -------------------------------------------------------------------------

    def load_scraper(self, source: SourceConfig):

        module = import_module(source.module)

        scraper_class = getattr(module, source.class_name)

        return scraper_class

    # -------------------------------------------------------------------------

    def summary(self):

        return {

            "version": self.version(),

            "enabled_sources": [
                s.name
                for s in self.enabled_sources()
            ],

            "build": self.build(),

            "publishing": self.publishing(),
        }


# -----------------------------------------------------------------------------
# Convenience API
# -----------------------------------------------------------------------------

_config = ConfigManager()


def get_config():

    return _config


def get_enabled_sources():

    return _config.enabled_sources()


def load_scraper(source: SourceConfig):

    return _config.load_scraper(source)
