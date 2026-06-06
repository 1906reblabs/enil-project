---
type: weekly-intelligence-report
week: <% tp.date.now("YYYY") %>-W<% tp.date.now("WW") %>
date: <% tp.date.now("YYYY-MM-DD") %>
schema: 1.0.0
opportunities_found: 0
total_effort_h: 0
tags: [enil, intelligence, weekly, <% tp.date.now("YYYY") %>]
---

# ENIL Weekly Intelligence Report — <% tp.date.now("YYYY") %>-W<% tp.date.now("WW") %>

> *"Every NSFAS crisis is a content event. Every DBE delay is a search spike. Every chaos event is a subscriber acquisition moment."*

← [[ENIL-MOC|← Home]] | [[04-Weekly-Logs/|All Weekly Logs]]

---

## 📡 Intelligence Summary

| Source | Status | Signal |
|--------|--------|--------|
| NSFAS Portal | 🔴 / 🟢 | — |
| NSFAS State | — | — new alerts (7d) |
| DBE | Normal / ⚠️ MATRIC SEASON | — new docs |
| APS Database | — programmes | Age: — days |
| Labour Market | — occupations | — critical shortages |

---

## 🔥 Antifragile Opportunities

> *Auto-populated by `weekly_orchestrator.py` Phase 1. Edit and action below.*

<!-- Paste orchestrator output here -->

*No critical opportunities detected — execute standard sprint rotation.*

---

## 📋 Content Queue

### 🔴 Urgent
*None this week.*

### 📅 This Week

- [ ] **Sprint rotation task** (— h)
  - *Details*
- [ ] **WhatsApp broadcast** (1h) — Springs / Germiston / Kempton Park
- [ ] **Revenue: follow up 1 SETA + 1 recruiter** (1h)

**Total estimated effort: — h**

---

## 💰 Revenue Actions This Week

**Recommended contact:** —
**Product:** —
**Template:** [[templates/outreach-seta|SETA]] | [[templates/tvet-outreach-template|TVET]] | [[templates/outreach-school-template|School]]

| Prospect | Action | Done? |
|---------|--------|-------|
| | | |

---

## 🏰 Moat Scores (Update from Orchestrator Output)

| Moat | Score | Change |
|------|-------|--------|
| Data Moat | /10 | |
| Distribution Moat | /10 | |
| Trust Moat | /10 | |
| SEO Moat | /10 | |
| **Antifragility** | **7/10** | |

---

## ⚙️ System Optimisation

### Data Freshness

| Source | Age | Status |
|--------|-----|--------|
| `dbe` | — days | |
| `nsfas` | — days | |
| `aps` | — days | |
| `labour` | — days | |

### Actions Required

- [ ] *None* — or paste from orchestrator output

### GitHub Actions (verify manually)

- [ ] [data_monitor.yml](https://github.com/ENIL-ZA/enil-data/actions/workflows/data_monitor.yml) — last run ✅
- [ ] [site_rebuild.yml](https://github.com/ENIL-ZA/enil-site/actions/workflows/site_rebuild.yml) — last run ✅
- [ ] [weekly_orchestration.yml](https://github.com/ENIL-ZA/enil-data/actions/workflows/weekly_orchestration.yml) — last run ✅

---

## 📝 Notes & Decisions

> *Free-form: what you noticed, what you decided, what changed.*



---

*Next run: <% tp.date.now("YYYY-MM-DD", 7) %> | Generated: <% tp.date.now("YYYY-MM-DD HH:mm") %> | Schema: 1.0.0*
