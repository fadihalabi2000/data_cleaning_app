import pandas as pd

import engine_childfix
from child_diag_filter import child_diagnosis_columns
from config.defaults import DEFAULT_SETTINGS


def child_context(columns):
    return {
        "filename": "children.xlsx", "clinic": "أطفال",
        "mapping": {
            "residency": "نوع الإقامة", "visit_type": "نوع الزيارة",
            "patient_id": "رقم تعريف المريض", "org_unit": None,
            "program_stage": None, "full_name": None, "birth_date": None,
            "event_date": None, "gender": None, "consultation_type": None,
            "imaging": None, "age": None,
        },
        "groups": {"diagnosis": columns, "labs": [], "imaging": [], "dressing": [],
                   "ncd": [], "ncd_na": [], "gyne_indicators": []},
        "settings": dict(DEFAULT_SETTINGS, custom_rules=[]),
    }


def test_child_imci_requires_all_columns_blank_and_keeps_common_rules():
    diagnosis = [
        "IMCI_NOT_APPLICABLE_UP_5_YEAR",
        "IMCI_NOT_APPLICABLE_FROM_2_TO_59_MONTH1",
        "IMCI_APPLICABLE_FROM_2_TO_59_MONTH2",
        "IMCI_NOT_APPLICABLE_UNDER_2_MONTH",
        "IMCI_APPLICABLE_UNDER_2_MONTH1",
    ]
    df = pd.DataFrame([
        ["خطأ", "", "", "", "", "", "", ""],
        ["مقيم", "جديد", "P2", "", "", "تشخيص", "", ""],
    ], columns=["نوع الإقامة", "نوع الزيارة", "رقم تعريف المريض", *diagnosis])
    errors, _ = engine_childfix.audit_dataframe(df, child_context(diagnosis))
    rules_by_row = errors.groupby("رقم الصف الأصلي")["اسم قاعدة التدقيق"].apply(set).to_dict()
    assert "غياب التشخيص" in rules_by_row[2]
    assert "نوع الإقامة" in rules_by_row[2]
    assert "نوع الزيارة مفقود" in rules_by_row[2]
    assert "رقم تعريف المريض مفقود" in rules_by_row[2]
    assert "غياب التشخيص" not in rules_by_row.get(3, set())


def test_child_drug_columns_are_excluded():
    columns = ["IMCI_APPLICABLE_UNDER_2_MONTH_Drugs3", "IMCI_APPLICABLE_UNDER_2_MONTH1"]
    assert child_diagnosis_columns(columns) == [columns[1]]
