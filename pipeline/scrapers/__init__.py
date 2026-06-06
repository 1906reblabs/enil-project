# ENIL Scrapers Package
# Place this file at: enil-data/pipeline/scrapers/__init__.py
from .dbe_scraper import DBEScraper
from .nsfas_monitor import NSFASMonitor
from .aps_scraper import APSScraper
from .labour_scraper import LabourScraper

__all__ = ["DBEScraper", "NSFASMonitor", "APSScraper", "LabourScraper"]
