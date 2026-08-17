import pandas as pd

import engine_generalfix
from config.defaults import DEFAULT_SETTINGS


def test_general_keeps_common_validation_rules():
    df = pd.DataFrame({
        "نوع الإقامة": ["قيمة خاطئة"],
        "نوع الزيارة": [""],
        "رقم تعريف المريض": [""],
        "NCD1": ["ضغط"],
    })
    context = {
        "filename": "general.xlsx",
        "clinic": "عامة",
        "mapping": {
            "residency": "نوع الإقامة",
            "visit_type": "نوع الزيارة",
            "patient_id": "رقم تعريف المريض",
            "org_unit": None,
            "program_stage": None,
            "full_name": None,
            "birth_date": None,
            "event_date": None,
            "gender": None,
            "consultation_type": None,
            "imaging": None,
            "age": None,
        },
        "groups": {
            "diagnosis": ["NCD1"],
            "labs": [], "imaging": [], "dressing": [], "ncd": ["NCD1"],
            "ncd_na": [], "gyne_indicators": [],
        },
        "settings": dict(DEFAULT_SETTINGS, custom_rules=[]),
    }
    errors, _ = engine_generalfix.audit_dataframe(df, context)
    rules = set(errors["اسم قاعدة التدقيق"])
    assert "نوع الإقامة" in rules
    assert "نوع الزيارة مفقود" in rules
    assert "رقم تعريف المريض مفقود" in rules
    assert "غياب التشخيص" not in rules
