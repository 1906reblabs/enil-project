"""
ENIL Master Data Schema  v1.0.0
================================
Pydantic models for every entity ENIL tracks.
This schema is the cross-reference no government portal provides:
  "If a learner in Springs takes Subject X in Grade 10,
   which doors does this open — or permanently close?"

Run standalone to validate:
  python schema.py
"""

from __future__ import annotations
from datetime import date, datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Enumerations ─────────────────────────────────────────────────────────────

class CredentialTrapClass(str, Enum):
    A = "A"  # Dead End: closes both university STEM AND high-demand TVET
    B = "B"  # Mismatch: university-eligible but no NSFAS + weak Ekurhuleni demand
    C = "C"  # Invisible: TVET paying more than BCom grad in 3 years
    D = "D"  # Optimal: satisfies APS + TVET + SETA-funded simultaneously


class NSFASState(str, Enum):
    PRE_APPLICATION     = "pre_application"       # Oct–Nov
    SUBMITTED_PENDING   = "submitted_pending"     # Nov–Jan
    PROVISIONALLY_FUNDED = "provisionally_funded" # Jan–Feb
    APPEALS_WINDOW      = "appeals_window"        # Mar–May  ← most critical
    DISBURSEMENT_ACTIVE = "disbursement_active"   # Feb–Nov
    CONTINUATION        = "continuation"          # Sept–Oct


class DemandSignal(str, Enum):
    CRITICAL_SHORTAGE = "CRITICAL_SHORTAGE"
    HIGH              = "HIGH"
    MEDIUM            = "MEDIUM"
    LOW               = "LOW"
    OVERSUPPLY        = "OVERSUPPLY"


class QualLevel(str, Enum):
    NCV_L2 = "NCV_L2"; NCV_L3 = "NCV_L3"; NCV_L4 = "NCV_L4"
    N1="N1"; N2="N2"; N3="N3"; N4="N4"; N5="N5"; N6="N6"
    DEGREE="DEGREE"; DIPLOMA="DIPLOMA"; CERTIFICATE="CERTIFICATE"


# ─── Subject / APS ────────────────────────────────────────────────────────────

class Subject(BaseModel):
    code:              str
    name:              str
    group:             Literal["compulsory", "elective"]
    aps_l4: int = Field(..., ge=0, le=7)
    aps_l5: int = Field(..., ge=0, le=7)
    aps_l6: int = Field(..., ge=0, le=7)
    aps_l7: int = Field(..., ge=0, le=7)
    is_maths_literacy: bool = False
    forecloses_engineering: bool = False   # True when is_maths_literacy=True


class SubjectCombo(BaseModel):
    combo_id:           str
    subjects:           List[Subject]
    aps_at_l5:          int
    aps_at_l6:          int
    trap_class:         CredentialTrapClass
    trap_explanation:   str
    recommended_action: str
    source_date:        date

    @model_validator(mode="after")
    def min_six_subjects(self):
        if len(self.subjects) < 6:
            raise ValueError("CAPS requires at least 6 subjects")
        return self


# ─── University Programmes ────────────────────────────────────────────────────

class UniversityProgramme(BaseModel):
    institution:        str
    faculty:            str
    programme:          str
    qual_type:          Literal["BSc","BCom","BA","BEng","BEd","Diploma","Certificate","Other"]
    min_aps:            int = Field(..., ge=0, le=42)
    required_subjects:  List[str] = []
    excluded_subjects:  List[str] = []   # e.g. ["Mathematical Literacy"]
    nsfas_eligible:     bool
    bursary_alts:       List[str] = []
    demand:             DemandSignal
    vacancy_count_2024: Optional[int] = None
    vacancy_source:     Optional[str] = None
    extracted_date:     date
    source_pdf_url:     Optional[str] = None


# ─── TVET ─────────────────────────────────────────────────────────────────────

class TVETCollege(BaseModel):
    name:           str
    location:       str   # e.g. "Springs"
    in_ekurhuleni:  bool = True


class TVETProgramme(BaseModel):
    prog_id:            str
    name:               str
    level:              QualLevel
    college:            TVETCollege
    duration_months:    int
    nsfas_eligible:     bool
    seta_funded:        bool
    seta_name:          Optional[str] = None
    annual_graduates:   Optional[int] = None
    annual_vacancies:   Optional[int] = None
    demand_gap:         Optional[int] = None   # vacancies − graduates
    salary_yr3_zar:     Optional[int] = None   # median ZAR/month at year 3
    extracted_date:     date

    @model_validator(mode="after")
    def calc_gap(self):
        if self.annual_vacancies and self.annual_graduates:
            self.demand_gap = self.annual_vacancies - self.annual_graduates
        return self


# ─── NSFAS ────────────────────────────────────────────────────────────────────

class NSFASAlert(BaseModel):
    alert_id:          str
    state:             NSFASState
    title:             str
    body:              str
    severity:          Literal["info","warning","critical"]
    action_required:   Optional[str] = None
    template_url:      Optional[str] = None
    circular_ref:      Optional[str] = None
    published_at:      datetime
    source_url:        Optional[str] = None


class NSFASStateRecord(BaseModel):
    state:             NSFASState
    period:            str
    description:       str
    crisis_points:     List[str] = []
    enil_actions:      List[str] = []
    appeal_grounds:    List[str] = []
    templates:         List[str] = []
    alerts:            List[NSFASAlert] = []


# ─── Labour Market ────────────────────────────────────────────────────────────

class Vacancy(BaseModel):
    job_title:          str
    ofo_code:           Optional[str] = None
    zone:               str           # e.g. "Springs Industrial"
    vacancy_count:      int
    source:             str
    scrape_date:        date
    median_salary_zar:  Optional[int] = None
    seta:               Optional[str] = None
    apprenticeship:     bool = False
    linked_tvet:        List[str] = []
    linked_uni:         List[str] = []


class DemandGapRow(BaseModel):
    occupation:         str
    linked_programme:   str
    annual_vacancies:   int
    annual_graduates:   int
    gap:                int             # positive = shortage
    signal:             DemandSignal
    seta:               Optional[str] = None
    salary_yr3_zar:     Optional[int] = None
    vs_bcom_premium_pct: Optional[float] = None
    generated_date:     date


# ─── Master Cross-Reference Row ───────────────────────────────────────────────

class ENILMasterRow(BaseModel):
    """
    One row = one subject combination →
    all university options + all TVET options +
    all labour market signals + trap classification.
    """
    row_id:          str
    combo:           SubjectCombo
    uni_programmes:  List[UniversityProgramme]
    tvet_programmes: List[TVETProgramme]
    vacancies:       List[Vacancy]
    trap_class:      CredentialTrapClass
    narrative:       str   # plain-language summary for WhatsApp/newsletter
    created_at:      datetime
    updated_at:      datetime
    schema_version:  str = "1.0.0"


# ─── Pipeline Run Record ──────────────────────────────────────────────────────

class PipelineRun(BaseModel):
    run_id:           str
    run_date:         datetime
    docs_processed:   int
    records_extracted:int
    records_failed:   int
    new_alerts:       int
    validation_errors:List[str] = []
    sources_checked:  List[str] = []
    duration_seconds: Optional[float] = None
    triggered_by:     Literal["cron","manual","webhook"]


# ─── Validation Entrypoint ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("ENIL Schema v1.0.0 — validation run\n")

    s = Subject(code="PHY", name="Physical Sciences", group="elective",
                aps_l4=4, aps_l5=5, aps_l6=6, aps_l7=7)

    t = TVETProgramme(
        prog_id="TVET_ELEC_SPR_001",
        name="Electrical Engineering N3",
        level=QualLevel.N3,
        college=TVETCollege(name="Springs TVET College", location="Springs"),
        duration_months=18, nsfas_eligible=True,
        seta_funded=True, seta_name="MERSETA",
        annual_graduates=120, annual_vacancies=340,
        salary_yr3_zar=32000, extracted_date=date.today()
    )

    print(f"Subject  → {s.name} | APS L6: {s.aps_l6}")
    print(f"TVETProg → {t.name} | Demand gap: {t.demand_gap}")
    print("\n✅ Schema validation passed.")
