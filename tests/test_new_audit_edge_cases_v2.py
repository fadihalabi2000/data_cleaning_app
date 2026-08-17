import pandas as pd

from engine_audit_v2 import _not_drug
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


def test_ncd_drug_columns_are_not_selected():
    columns = ["NCD1_Hypertension", "NCD1_Hypertension_Drug", "NCD_Drugs3"]
    assert [column for column in columns if _not_drug(column)] == ["NCD1_Hypertension"]


def test_different_identity_is_not_duplicate():
    df = pd.DataFrame({
        "id": ["100", "500"], "name": ["محمد أحمد علي", "محمد أحمد علي"],
        "birth": ["1990-01-01", "2010-01-01"], "gender": ["ذكر", "أنثى"],
        "residency": ["مقيم", "نازح"], "age": [36, 16],
    })
    frame, _ = validate_possible_duplicate_patients(df, duplicate_context())
    assert frame.empty
