import pandas as pd

from app_quality14 import detected_groups_without_drugs
from validators.duplicate_patients import validate_possible_duplicate_patients


def duplicate_context():
    return {
        "filename": "sample.xlsx", "clinic": "عامة",
        "mapping": {
            "patient_id": "id", "full_name": "name", "birth_date": "birth",
            "gender": "gender", "residency": "residency", "age": "age",
            "org_unit": None, "program_stage": None,
        },
        "groups": {},
        "settings": {"duplicate_birthdate_max_days": 365, "duplicate_min_score": 70},
    }


def test_ncd_drug_columns_are_not_selected(monkeypatch):
    # نعزل الاختبار عن كاش دالة الاكتشاف الأصلية ونثبت شرط الاستبعاد العام.
    columns = ["NCD1_Hypertension", "NCD1_Hypertension_Drug", "NCD_Drugs3"]
    groups = detected_groups_without_drugs(columns)
    selected = groups.get("ncd", []) + groups.get("ncd_na", []) + groups.get("diagnosis", [])
    assert not any("drug" in str(column).casefold() for column in selected)


def test_different_identity_is_not_duplicate():
    df = pd.DataFrame({
        "id": ["100", "500"], "name": ["محمد أحمد علي", "محمد أحمد علي"],
        "birth": ["1990-01-01", "2010-01-01"], "gender": ["ذكر", "أنثى"],
        "residency": ["مقيم", "نازح"], "age": [36, 16],
    })
    frame, _ = validate_possible_duplicate_patients(df, duplicate_context())
    assert frame.empty
