import pandas as pd

import engine_audit_v2
from validators.women_anc_duplicate import (
    RULE_NAME,
    canonical_anc_visit,
    install_women_rule,
    validate_duplicate_anc_same_day,
)


def context():
    return {
        "filename": "gynecology.xls",
        "clinic": "نسائية",
        "mapping": {
            "patient_id": "id",
            "full_name": "name",
            "birth_date": "birth",
            "event_date": "event",
            "anc_visit": "anc",
            "org_unit": None,
            "program_stage": None,
        },
        "groups": {},
        "settings": {},
    }


def test_canonical_anc_variants():
    assert canonical_anc_visit("ANC 1") == "ANC 1"
    assert canonical_anc_visit("ANC-1") == "ANC 1"
    assert canonical_anc_visit("1") == "ANC 1"
    assert canonical_anc_visit("الزيارة الأولى") == "ANC 1"


def test_detects_all_duplicate_rows_same_patient_visit_and_day():
    df = pd.DataFrame({
        "id": ["P-10", "P-10", "P-10"],
        "name": ["سارة أحمد"] * 3,
        "birth": ["1990-01-01"] * 3,
        "event": ["2026-09-01 08:00", "2026-09-01 15:00", "2026-09-02"],
        "anc": ["ANC 1", "ANC-1", "ANC 1"],
    })
    frame, skipped = validate_duplicate_anc_same_day(df, context())
    assert skipped == []
    assert frame["رقم الصف الأصلي"].tolist() == [2, 3]
    assert frame["اسم قاعدة التدقيق"].eq(RULE_NAME).all()
    assert frame["درجة الأهمية"].eq("High").all()


def test_does_not_flag_different_day_visit_or_patient():
    df = pd.DataFrame({
        "id": ["P-10", "P-10", "P-20"],
        "name": ["سارة أحمد", "سارة أحمد", "مريم خالد"],
        "birth": ["1990-01-01", "1990-01-01", "1995-01-01"],
        "event": ["2026-09-01", "2026-09-02", "2026-09-01"],
        "anc": ["ANC 1", "ANC 1", "ANC 1"],
    })
    frame, skipped = validate_duplicate_anc_same_day(df, context())
    assert skipped == []
    assert frame.empty


def test_rule_is_installed_without_replacing_existing_women_rules(monkeypatch):
    existing = pd.DataFrame({"اسم قاعدة التدقيق": ["قاعدة نسائية موجودة"]})

    def base(df, ctx):
        return [existing], []

    monkeypatch.setattr(engine_audit_v2, "run_women_rules", base)
    monkeypatch.delattr(engine_audit_v2, "_anc_duplicate_base_run_women_rules", raising=False)
    install_women_rule(engine_audit_v2)
    df = pd.DataFrame({
        "id": ["P-1", "P-1"], "name": ["سارة", "سارة"],
        "birth": ["1990-01-01", "1990-01-01"],
        "event": ["2026-09-01", "2026-09-01"], "anc": ["ANC 2", "ANC 2"],
    })
    frames, skipped = engine_audit_v2.run_women_rules(df, context())
    assert skipped == []
    assert frames[0].iloc[0]["اسم قاعدة التدقيق"] == "قاعدة نسائية موجودة"
    assert frames[1]["اسم قاعدة التدقيق"].eq(RULE_NAME).all()
