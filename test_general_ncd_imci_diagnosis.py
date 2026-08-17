import pandas as pd

import engine_generalfix


def test_general_missing_diagnosis_requires_all_families_blank(monkeypatch):
    columns = [
        "NCD 1",
        "NCD_Not_Applicable 2",
        "IMCI_NOT_APPLICABLE_UP_5_YEAR",
        "IMCI_APPLICABLE_FROM_2_TO_59_MONTH 3",
        "IMCI_APPLICABLE_UNDER_2_MONTH 1",
    ]
    df = pd.DataFrame([
        ["", "", "", "", ""],
        ["ضغط", "", "", "", ""],
        ["", "نعم", "", "", ""],
        ["", "", "", "", "تشخيص طفل"],
    ], columns=columns)
    monkeypatch.setattr(
        engine_generalfix,
        "audit_existing",
        lambda frame, context: (pd.DataFrame(), pd.DataFrame()),
    )
    context = {
        "filename": "general.xlsx",
        "clinic": "عامة",
        "mapping": {},
        "groups": {"diagnosis": []},
        "settings": {},
    }
    errors, skipped = engine_generalfix.audit_dataframe(df, context)
    assert skipped.empty
    assert list(errors["رقم الصف الأصلي"]) == [2]
    assert errors.iloc[0]["اسم قاعدة التدقيق"] == "غياب التشخيص"
    assert engine_generalfix.general_diagnosis_columns(columns) == columns
