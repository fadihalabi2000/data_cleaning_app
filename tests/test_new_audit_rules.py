import pandas as pd

from findings_v2 import enrich_findings
from validators.common_rules import validate_negative_or_future_age
from validators.duplicate_patients import validate_possible_duplicate_patients
from validators.gender_rules import predict_gender, validate_gender_consistency
from validators.women_rules_v2 import validate_anc1_not_phone, validate_pregnancy_type_consistency


def context(clinic="عامة", **settings):
    return {
        "filename": "sample.xlsx", "clinic": clinic,
        "mapping": {
            "patient_id": "id", "full_name": "name", "birth_date": "birth",
            "event_date": "event", "gender": "gender", "residency": "residency",
            "age": "age", "anc_visit": "anc", "consultation_type": "consultation",
            "org_unit": "org", "program_stage": "stage",
        },
        "groups": {},
        "settings": {"max_age": 100, "duplicate_birthdate_max_days": 365, "duplicate_min_score": 70,
                     "phone_consultation_values": ["هاتفية"], **settings},
    }


def test_negative_age_is_error():
    df = pd.DataFrame({"birth": ["2030-01-01"], "event": ["2026-01-01"]})
    frame, _ = validate_negative_or_future_age(df, context())
    assert len(frame) == 1
    assert frame.iloc[0]["درجة الأهمية"] == "High"


def test_anc_one_phone_is_error_and_physical_is_ok():
    df = pd.DataFrame({"anc": ["ANC 1", "الزيارة الأولى"], "consultation": ["هاتفية", "فيزيائية"]})
    frame, _ = validate_anc1_not_phone(df, context("نسائية"))
    assert frame["رقم الصف الأصلي"].tolist() == [2]


def test_pregnancy_type_change_exports_all_patient_visits():
    df = pd.DataFrame({
        "id": ["A", "A", "A"], "name": ["سارة احمد"] * 3,
        "birth": ["1990-01-01"] * 3, "event": ["2026-01-01", "2026-02-01", "2026-03-01"],
        "anc": ["ANC 1", "ANC 2", "ANC 3"], "preg": ["مفرد", "متعدد", "مفرد"],
    })
    frame, _ = validate_pregnancy_type_consistency(df, context("نسائية", pregnancy_type_column="preg"))
    assert len(frame) == 3
    assert frame["سبب الخطأ"].str.contains("حمل مفرد").all()
    assert frame["سبب الخطأ"].str.contains("حمل متعدد").all()


def test_strong_duplicate_and_unrelated_pair():
    df = pd.DataFrame({
        "id": ["11", "22", "33"], "name": ["أحمد محمد علي", "احمد محمد على", "سارة خالد"],
        "birth": ["1990-01-01", "1990-01-02", "2000-01-01"], "gender": ["ذكر", "ذكر", "أنثى"],
        "residency": ["مقيم", "مقيم", "نازح"], "age": [36, 36, 26],
    })
    frame, _ = validate_possible_duplicate_patients(df, context())
    assert len(frame) == 1
    assert frame.iloc[0]["Patient ID الثاني"] == "22"
    assert frame.iloc[0]["درجة التشابه الإجمالية"] >= 90


def test_gender_high_confidence_mismatch_and_uncertain_name():
    df = pd.DataFrame({"name": ["محمد علي", "زغروت سالم"], "gender": ["أنثى", "ذكر"]})
    frame, _ = validate_gender_consistency(df, context())
    assert len(frame) == 1
    assert frame.iloc[0]["مستوى الثقة"] == "عالي"
    assert predict_gender("زغروت سالم")["confidence"] == "غير مؤكد"


def test_metadata_columns_are_added():
    source = pd.DataFrame({"اسم قاعدة التدقيق": ["غياب التشخيص"], "درجة الحالة": ["خطأ"]})
    result = enrich_findings(source)
    assert result.iloc[0]["تصنيف الملاحظة"] == "خطأ"
    assert result.iloc[0]["درجة الأهمية"] == "High"
