---
type: hub
title: Revenue Hub
tags: [enil, revenue, b2b, pipeline, products]
updated: <% tp.date.now("YYYY-MM-DD") %>
---

# 💰 Revenue Hub

> "The constraint is non-negotiable: learners and parents never pay. All monetisation is B2B or institutional — extracting value from entities that currently have a data access problem that ENIL solves."

← [[ENIL-MOC|← Home]]

---

## Revenue Model

| Path | Customer | Price | Year 1 Target | Margin | Status |
|------|---------|-------|--------------|--------|--------|
| B2B Data Licensing | SETAs + Recruiters | R8k–R15k/yr (SETA), R3–6k/mo (recruiter) | R80,000 | ~95% | 🟡 Prospecting |
| Premium Briefs | Private schools + advisors | R8k–R15k/yr | R60,000 | ~90% | 🟡 Prospecting |
| TVET Dashboards | TVET colleges | R25k setup + R8k/yr | R99,000 | ~85% | 🟡 Prospecting |
| **TOTAL** | | | **R215,000+** | | |

---

## B2B Pipeline

### Stage Definitions

| Stage | Meaning | Next Action |
|-------|---------|------------|
| `identified` | Know who they are, no contact yet | Draft outreach email |
| `contacted` | First email/call sent | Wait 5 days then follow up |
| `demo_scheduled` | Meeting booked | Prepare sample report/prototype |
| `proposal_sent` | Formal proposal delivered | Follow up in 7 days |
| `negotiating` | In active discussion | Close within 14 days |
| `won` | Contract signed | Deliver product; schedule check-in |
| `lost` | Declined | Note reason; re-approach in 6 months |

---

## SETAs

### P001 — MERSETA Gauteng Region
**Stage:** `identified`
**Value:** R12,000/year
**Product:** [[#Product-A-TVET-Dashboard|B2B Data Intelligence Report (quarterly)]]
**Notes:** Artisan gap data directly matches MERSETA mandate. Their funding allocation decisions directly map to the vacancy gaps in our gap table. Priority contact.
**Contact:** *(find via merseta.org.za/contact)*
**Template:** [[templates/outreach-seta|SETA Outreach Template]]
→ Full prospect note: [[06-Prospects/P001-MERSETA]]

### P002 — EWSETA
**Stage:** `identified`
**Value:** R10,000/year
**Product:** B2B Data Intelligence Report (quarterly)
**Notes:** Electrical sector — perfect match with Springs/Germiston electrician vacancy data. EWSETA funds electrical artisan learnerships; our gap data justifies allocation.
→ Full prospect note: [[06-Prospects/P002-EWSETA]]

---

## Industrial Recruiters

### P003 — Scaw Metals (Springs)
**Stage:** `identified`
**Value:** R5,000/month
**Product:** Monthly TVET Talent Pipeline Report
**Notes:** Springs plant — direct consumer of electrical and mechanical TVET graduates. Monthly report shows them which colleges are producing which candidates.
→ [[06-Prospects/P003-Scaw-Metals]]

### P004 — Rand Refinery (Germiston)
**Stage:** `identified`
**Value:** R5,000/month
**Product:** Monthly TVET Talent Pipeline Report
**Notes:** Artisan-heavy workforce. Instrumentation and electrical artisans are their highest need. Germiston base = direct match to our vacancy data.
→ [[06-Prospects/P004-Rand-Refinery]]

### P005 — OR Tambo Logistics Cluster
**Stage:** `identified`
**Value:** R4,000/month
**Product:** Monthly TVET Talent Pipeline Report
**Notes:** Kempton Park zone. Diesel mechanic and aviation maintenance artisan demand. Logistics sector expanding with OR Tambo growth.
→ [[06-Prospects/P005-OR-Tambo-Logistics]]

---

## Private Schools

### P006 — St Dunstan's College (Benoni)
**Stage:** `identified`
**Value:** R12,000/year
**Product:** [[#Product-C-Premium-Brief|Premium Navigation Brief (annual)]]
**Notes:** Grade 9–12 subject choice mapping + branded Grade 9 parent evening deck. Benoni corridor. Independent school with active parent community.
→ [[06-Prospects/P006-St-Dunstans]]

### P007 — Edenglen High (Edenvale)
**Stage:** `identified`
**Value:** R12,000/year
**Product:** Premium Navigation Brief (annual)
**Notes:** Edenvale corridor. Strong parent engagement. Near industrial zones — TVET pathway messaging is directly relevant.
→ [[06-Prospects/P007-Edenglen-High]]

### P008 — Boksburg High School
**Stage:** `identified`
**Value:** R10,000/year
**Product:** Premium Navigation Brief (annual)
**Notes:** Large Grade 9–10 cohort. Boksburg industrial zone.
→ [[06-Prospects/P008-Boksburg-High]]

---

## TVET Colleges

> Highest unit economics. R25k setup + R8k/year. Most counterintuitive but highest-value revenue path.

### P009 — Springs TVET College
**Stage:** `identified`
**Value:** R33,000 (setup + Year 1)
**Product:** [[#Product-A-TVET-Dashboard|Employment Outcomes Dashboard]]
**Notes:** Priority 1. Springs industrial cluster = perfect match for their engineering graduates. Principal has strong incentive: demonstrating graduate employment to DHET directly affects funding.
→ [[06-Prospects/P009-Springs-TVET]]

### P010 — Ekurhuleni West TVET College
**Stage:** `identified`
**Value:** R33,000 (setup + Year 1)
**Product:** Employment Outcomes Dashboard
**Notes:** Largest TVET in the corridor. Principal has political visibility — an employment dashboard is a public-facing achievement.
→ [[06-Prospects/P010-Ekurhuleni-West-TVET]]

### P011 — Ekurhuleni East TVET College
**Stage:** `identified`
**Value:** R33,000 (setup + Year 1)
**Product:** Employment Outcomes Dashboard
**Notes:** Germiston base. Strong engineering + business programmes. Germiston vacancy data directly matches their output.
→ [[06-Prospects/P011-Ekurhuleni-East-TVET]]

---

## Product Specifications

### Product A — TVET Employment Outcomes Dashboard

**What it is:** A branded static GitHub Pages microsite (college's own colours + logo) showing ENIL vacancy data filtered to their specific programmes. Auto-updated quarterly from the ENIL pipeline. The college provides graduate employment survey data in exchange — feeding back into ENIL's schema.

**Pricing:** R25,000 setup + R8,000/year maintenance
**Production cost:** 12–16h first edition; 2h per quarterly update
**Margin:** ~85% after setup; ~96% recurring
**Moat:** College becomes dependent on the dashboard for DHET funding justifications. Switching cost = losing their marketing asset.

**Deliverables:**
- Branded microsite at `college-name.enil.co.za/outcomes/`
- Programme-by-programme vacancy demand display
- Annual graduate survey integration
- Quarterly data refresh

---

### Product B — B2B Data Intelligence Report

**What it is:** Quarterly PDF report (20–30 pages). Designed for SETA offices and metro economic development departments who need structured data to justify learnership funding allocations.

**Pricing:** R8,000–R15,000/organisation/year (4 reports)
**Production cost:** 4–6h per quarter (template-based after first edition)
**Margin:** ~95%

**Report contents:**
- Ekurhuleni TVET output vs vacancy gap table (updated)
- Top 10 demand occupations with OFO codes
- Graduate pipeline forecast by programme and college
- Recommended learnership funding allocation priorities
- Labour market trend analysis (quarterly change)

---

### Product C — Premium Navigation Brief

**What it is:** Annual package for private schools. Replaces the generic "career advice" session with ENIL-powered, school-specific, data-driven guidance.

**Pricing:** R8,000–R15,000/school/year | R2,500/year (independent advisor licence)
**Production cost:** 8–12h first edition; 2–3h quarterly updates
**Margin:** ~90%

**Annual package includes:**
1. Subject choice mapping: every CAPS combination at the school vs full ENIL schema
2. Annual "Career Trajectory Deck" — 15-slide PowerPoint for Grade 9 parent evening, branded to school
3. Quarterly NSFAS + university deadline calendar (school-specific relevant dates)
4. On-call response to time-sensitive NSFAS/APS queries (email, 48h turnaround)

---

## Revenue Milestones

- [ ] **R0 → R25,000** First TVET dashboard setup fee *(target: Month 2)*
- [ ] **R25k → R75k** First SETA contract + second TVET dashboard *(target: Month 4)*
- [ ] **R75k → R150k** First school retainer + third TVET + first recruiter monthly *(target: Month 8)*
- [ ] **R150k → R215k+** Full Year 1 target: 3 TVET + 2 SETAs + 3 recruiters + 2 schools *(target: Month 12)*

---

*← [[Systems-Hub]] | [[ENIL-MOC|Home]] | [[Content-Hub]] →*
