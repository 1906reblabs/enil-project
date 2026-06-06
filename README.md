# ENIL — Education Navigation Intelligence Layer

> *"Build the decoder ring. The cipher will never be solved — the system has no incentive to become legible. That is your competitive advantage."*

**ENIL** is a free education navigation platform for Grade 10–12 learners in the Ekurhuleni corridor (Springs · Germiston · Kempton Park). It translates opaque government data — APS requirements, NSFAS states, TVET pathways, labour market gaps — into plain-language, actionable guidance.

**Learners and parents never pay.** Revenue is B2B and institutional.

---

## Live Site

🌐 **[1906reblabs.github.io/enil-project](https://1906reblabs.github.io/enil-project)**

| Tool | URL | Monthly Search Volume |
|------|-----|----------------------|
| APS Calculator | `/aps-calculator/` | 6–10k |
| Credential Trap Detector | `/credential-trap/` | 3–5k |
| NSFAS Chaos Translator | `/nsfas/` | 8–12k |
| Ekurhuleni Labour Map | `/ekurhuleni-map/` | 800–1.2k |

---

## Repository Structure

```
enil-project/
├── site/                        ← Static site (GitHub Pages)
│   ├── index.html               ← Homepage
│   ├── aps-calculator/          ← APS Calculator tool
│   ├── credential-trap/         ← Subject combination classifier
│   ├── nsfas/                   ← NSFAS state machine + appeal guide
│   ├── ekurhuleni-map/          ← TVET vs vacancy gap table
│   ├── data/                    ← Data downloads page
│   └── about/                   ← About page
│
├── pipeline/                    ← Data extraction pipeline
│   ├── pipeline.py              ← Main orchestrator
│   ├── schema.py                ← Pydantic data models
│   ├── scrapers/
│   │   ├── dbe_scraper.py       ← DBE matric report monitor
│   │   ├── nsfas_monitor.py     ← NSFAS state machine + alerts
│   │   ├── aps_scraper.py       ← 26 university APS extractor
│   │   └── labour_scraper.py    ← Ekurhuleni vacancy gap table
│   └── data/                    ← Pipeline output (auto-generated)
│       ├── dbe/
│       ├── nsfas/
│       ├── aps/
│       └── labour/
│
├── obsidian/                    ← Obsidian vault (operating brain)
│   ├── 00-MOC/ENIL-MOC.md       ← Home note — start here every Monday
│   ├── 01-Intelligence/         ← NSFAS, DBE, APS, Labour hubs
│   ├── 02-Systems/              ← GitHub Actions, pipeline health
│   ├── 03-Revenue/              ← B2B pipeline, products, pricing
│   ├── 04-Weekly-Logs/          ← Auto-generated Monday reports
│   ├── 05-Content/              ← Page drafts, newsletter editions
│   ├── 06-Prospects/            ← 11 B2B prospect notes (P001–P011)
│   └── templates/               ← Outreach, newsletter, prospect templates
│
├── .github/workflows/
│   ├── data_monitor.yml         ← Daily 06:00 SAST pipeline run
│   ├── site_rebuild.yml         ← Deploy site/ to GitHub Pages
│   └── weekly_orchestration.yml ← Monday intelligence + revenue loop
│
├── weekly_orchestrator.py       ← Weekly intelligence loop (run locally Mondays)
├── revenue_pipeline.json        ← B2B prospect tracking (auto-updated)
└── requirements.txt             ← Python dependencies
```

---

## Automated Workflows

| Workflow | Schedule | What It Does |
|----------|----------|-------------|
| `data_monitor.yml` | Daily 06:00 SAST | Pipeline run → validate → commit data → trigger site rebuild → NSFAS portal check |
| `site_rebuild.yml` | On data push + Sundays | Copy data → generate sitemap → deploy `site/` to GitHub Pages |
| `weekly_orchestration.yml` | Monday 06:00 SAST | Intelligence scan → content queue → revenue pipeline → moat scores → weekly report |

Weekly reports are committed to `obsidian/04-Weekly-Logs/YYYY-WNN.md` automatically.

---

## Local Setup

### Prerequisites
- Python 3.11+
- Git

### Install

```bash
git clone https://github.com/1906reblabs/enil-project.git
cd enil-project

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium

# System deps (Ubuntu/Debian)
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng

# System deps (macOS)
brew install tesseract tesseract-lang
```

### Run the pipeline

```bash
# Validate schema (no writes)
python pipeline/schema.py

# Dry run (validate all scrapers, no file writes)
python pipeline/pipeline.py --dry-run

# Full pipeline run (generates all data files)
python pipeline/pipeline.py --source all

# Single source
python pipeline/pipeline.py --source nsfas

# Weekly intelligence report (run every Monday)
python weekly_orchestrator.py

# Dry run of weekly report
python weekly_orchestrator.py --dry-run
```

### View the site locally

```bash
# Python built-in server from the site/ directory
cd site && python -m http.server 8000
# Open: http://localhost:8000
```

---

## Data Sources

| Source | Data | Update Frequency |
|--------|------|-----------------|
| MERSETA Annual Report | Artisan vacancy counts, OFO codes | Annual (March) |
| EWSETA Annual Report | Electrical sector vacancies | Annual |
| Ekurhuleni IDP | Metro-level employment data | Annual (March) |
| DHET TVET Output | Graduate counts by college + programme | Annual |
| DBE NSC Results | Provincial pass rates, subject performance | Annual (January) |
| University Prospectuses | APS requirements, programme entry criteria | Annual |
| PNet / LinkedIn | Live vacancy scraping (Ekurhuleni) | Daily (pipeline) |
| myNSFAS Portal | Portal status, state detection | Daily (pipeline) |
| NSFAS Circulars | New circular detection | Daily (pipeline) |

All datasets are released under **CC BY 4.0** — freely usable with attribution.

---

## B2B Revenue Model

ENIL is free for learners. Revenue comes from institutional products:

| Product | Customer | Price |
|---------|---------|-------|
| Employment Outcomes Dashboard | TVET colleges | R25,000 setup + R8,000/yr |
| Data Intelligence Report (quarterly) | SETAs | R8,000–R15,000/yr |
| Premium Navigation Brief | Private schools | R8,000–R15,000/yr |
| TVET Talent Pipeline Report | Industrial recruiters | R3,000–R6,000/mo |

**Year 1 pipeline target: R215,000+** across 11 identified prospects.

---

## The Three Non-Obvious Truths

1. **R45k/month** — artisan (electrician/millwright) median salary at year 5 vs R28k for BCom graduates in the same period. South Africa has a critical shortage of artisans and a surplus of BCom graduates.

2. **~43%** — NSFAS appeal success rate when the correct rejection code grounds are cited. Most appeals fail procedurally, not on merit.

3. **Mathematical Literacy in Grade 10** permanently forecloses both university engineering programmes and all NATED N1-N3 TVET artisan pathways — the highest-demand, highest-paying route in Ekurhuleni. Most learners are not told this.

---

## The Competitive Moat

| Moat | Why It's Defensible |
|------|-------------------|
| **Data** | Ekurhuleni gap table cross-references 4 datasets never combined publicly. Months of pipeline work to replicate. |
| **Distribution** | Trilingual WhatsApp channels (Zulu/Sotho/English) built for specific communities. Google cannot replicate this. |
| **Trust** | In a low-trust environment, the entity that is consistently accurate in plain language becomes the default. |
| **Antifragility** | Every NSFAS crisis, every DBE delay, every portal crash makes ENIL more valuable — not less. |

---

## Obsidian Vault

The `obsidian/` folder is the operating brain of the project. Open it in [Obsidian](https://obsidian.md) (free):

1. Obsidian → Open folder as vault → select `obsidian/`
2. Install plugins: **Templater** + **Dataview** + **Calendar**
3. Pin `00-MOC/ENIL-MOC.md` — this is your Monday command centre
4. Run `python weekly_orchestrator.py` every Monday → paste output into the week's log

---

## Contributing

This is a public-interest project. Data corrections, new subject combination classifications, and NSFAS state updates are welcome via pull request.

**All learner-facing content must remain free.** No exceptions.

---

## Licence

- **Code:** MIT
- **Data:** CC BY 4.0
- **Attribution:** ENIL Navigation Intelligence — enil.co.za

---

*Built for the learners of Springs, Germiston, and Kempton Park.*
