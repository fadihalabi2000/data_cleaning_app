import pandas as pd

from clinic_detection import weighted_suggest_clinic
from engine_v4 import audit_dataframe


def test_maternity_filename_is_detected():
    assert weighted_suggest_clinic("Maternity-8-2026.xls", [], []) == "مخاض"


def test_maternity_runs_common_rules_without_diagnosis_rule():
    df = pd.DataFrame({
        "org": ["مركز"], "stage": ["Maternity"], "id": ["M-1"],
        "name": ["سارة أحمد"], "birth": ["1990-01-01"], "event": ["2026-08-01"],
        "residency": ["قيمة غير مقبولة"], "visit": ["جديد"],
        "consultation": ["فيزيائية"], "age": [36],
    })
    mapping = {
        "org_unit": "org", "program_stage": "stage", "patient_id": "id",
        "full_name": "name", "birth_date": "birth", "event_date": "event",
        "gender": None, "residency": "residency", "visit_type": "visit",
        "consultation_type": "consultation", "imaging": None, "age": "age",
        "injury_type": None, "anc_visit": None,
    }
    ctx = {
        "filename": "Maternity.xls", "clinic": "مخاض", "mapping": mapping,
        "groups": {"imaging": [], "labs": [], "diagnosis": []},
        "settings": {"allowed_residency": ["مقيم", "نازح"], "max_age": 100,
                     "accepted_diagnosis_values": [], "phone_consultation_values": ["هاتفية"]},
    }
    errors, skipped = audit_dataframe(df, ctx)
    assert "نوع الإقامة" in errors["اسم قاعدة التدقيق"].tolist()
    assert "غياب التشخيص" not in skipped.get("اسم قاعدة التدقيق", pd.Series(dtype=str)).tolist()
