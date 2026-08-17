"""طبقة التدقيق الموسعة مع إبقاء محرك القواعد السابق دون تعديل."""

from copy import deepcopy

import pandas as pd

from engine_childfix import audit_dataframe as audit_existing
from findings_v2 import enrich_findings
from validators.common_rules import run_common_rules
from validators.women_rules_v2 import run_women_rules


REPLACED_RULES = {
    "اشتباه بتعارض الجنس",
    "عمر غير منطقي",
    "عدم تطابق الجنس",
    "العمر السالب أو تاريخ الميلاد المستقبلي",
    "عمر يتجاوز الحد المنطقي",
    "المستفيدون المحتمل تكرار تسجيلهم",
    "ثبات نوع الحمل",
    "ANC 1 مسجلة هاتفياً",
}


def _not_drug(column):
    return "drug" not in str(column).casefold()


def _safe_frame(rows):
    return rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows or [])


def audit_dataframe(df, context):
    local = dict(context)
    local["mapping"] = dict(context.get("mapping", {}))
    local["settings"] = deepcopy(context.get("settings", {}))
    local["groups"] = deepcopy(context.get("groups", {}))
    local["settings"].setdefault("duplicate_birthdate_max_days", 365)
    local["settings"].setdefault("duplicate_min_score", 70)
    local["settings"].setdefault("phone_consultation_values", ["هاتفية", "هاتف", "Phone", "Telephone"])

    # أعمدة الأدوية ليست تشخيصاً، مهما كان ترقيم اللاحقة (_Drug, _Drugs3...).
    if local.get("clinic") == "داخلية / NCD":
        for key in ("ncd", "ncd_na", "diagnosis"):
            local["groups"][key] = [col for col in local["groups"].get(key, []) if _not_drug(col)]

    errors, skipped = audit_existing(df, local)
    errors, skipped = _safe_frame(errors), _safe_frame(skipped)
    if not errors.empty and "اسم قاعدة التدقيق" in errors:
        errors = errors[~errors["اسم قاعدة التدقيق"].isin(REPLACED_RULES)].copy()
    if not skipped.empty and "اسم قاعدة التدقيق" in skipped:
        skipped = skipped[~skipped["اسم قاعدة التدقيق"].isin(REPLACED_RULES)].copy()

    frames, skipped_rows = run_common_rules(df, local)
    if local.get("clinic") == "نسائية":
        women_frames, women_skipped = run_women_rules(df, local)
        frames.extend(women_frames)
        skipped_rows.extend(women_skipped)
    if frames:
        errors = pd.concat([errors, *frames], ignore_index=True, sort=False)
    if skipped_rows:
        skipped = pd.concat([skipped, pd.DataFrame(skipped_rows)], ignore_index=True, sort=False)

    errors = enrich_findings(errors)
    if not errors.empty:
        # لا نحذف أزواج الاشتباه المختلفة لنفس المريض.
        ordinary = errors[errors["اسم قاعدة التدقيق"].ne("المستفيدون المحتمل تكرار تسجيلهم")]
        duplicates = errors[errors["اسم قاعدة التدقيق"].eq("المستفيدون المحتمل تكرار تسجيلهم")]
        ordinary = ordinary.drop_duplicates(subset=["اسم الملف", "رقم الصف الأصلي", "اسم قاعدة التدقيق"])
        if not duplicates.empty:
            duplicates = duplicates.drop_duplicates(subset=["اسم الملف", "رقم الصف الأصلي", "رقم الصف الثاني", "اسم قاعدة التدقيق"])
        errors = pd.concat([ordinary, duplicates], ignore_index=True, sort=False)
    return errors, skipped
