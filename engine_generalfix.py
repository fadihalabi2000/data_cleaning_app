from copy import deepcopy

import pandas as pd

from engine_quality2 import audit_dataframe as audit_existing
from utils.cleaning import clean_text, normalized
from validators.base import result_rows

GENERAL_DIAGNOSIS_FAMILIES = (
    "ncd",
    "ncd_not_applicable",
    "imci_not_applicable_up_5_year",
    "imci_applicable_from_2_to_59_month",
    "imci_applicable_under_2_month",
)

FOREIGN_CLINIC_RULES = {
    "اكتمال تشخيص الأطفال",
    "عمر مراجع عيادة الأطفال",
    "عمر غير مناسب لعيادة الأطفال",
    "تشخيص NCD مفقود",
    "تناقض تشخيص NCD",
    "بيانات الضماد مفقودة",
    "عمر غير مناسب للعيادة النسائية",
    "تنظيم الأسرة مع زيارة حمل ANC",
    "تسلسل زيارات الحمل",
}


def is_general_diagnosis(column):
    value = normalized(column).replace(" ", "_").replace("-", "_")
    # نفحص العائلات الأطول أولاً، ثم NCD الذي يشمل NCD المرقمة.
    return any(family in value for family in GENERAL_DIAGNOSIS_FAMILIES)


def general_diagnosis_columns(columns):
    return [column for column in columns if is_general_diagnosis(column)]


def audit_dataframe(df, context):
    if context["clinic"] != "عامة":
        return audit_existing(df, context)

    local = dict(context)
    local["groups"] = deepcopy(context["groups"])
    detected = general_diagnosis_columns(df.columns)
    local["groups"]["diagnosis"] = detected or list(local["groups"].get("diagnosis", []))
    errors, skipped = audit_existing(df, local)

    replaced_rules = {"غياب التشخيص", "اكتمال التشخيص العام", *FOREIGN_CLINIC_RULES}
    if not errors.empty:
        errors = errors[~errors["اسم قاعدة التدقيق"].isin(replaced_rules)].copy()
    if not skipped.empty:
        skipped = skipped[~skipped["اسم قاعدة التدقيق"].isin(replaced_rules)].copy()

    columns = local["groups"].get("diagnosis", [])
    if not columns:
        row = {
            "اسم الملف": local["filename"],
            "نوع العيادة": "عامة",
            "اسم قاعدة التدقيق": "غياب التشخيص",
            "سبب التجاوز": "لم يتم اكتشاف أعمدة NCD أو IMCI الخمسة في الملف",
        }
        skipped = pd.concat([skipped, pd.DataFrame([row])], ignore_index=True)
        return errors, skipped

    # الشرط AND: لا نسجل الخطأ إلا عندما تكون كل أعمدة العائلات الخمس فارغة معاً.
    all_blank = ~df[columns].apply(lambda series: series.map(clean_text).ne("")).any(axis=1)
    frame = result_rows(
        df,
        all_blank,
        local,
        "غياب التشخيص",
        "جميع أعمدة NCD وNCD_Not_Applicable وIMCI المحددة فارغة في السجل نفسه",
        columns,
    )
    if not frame.empty:
        frame["تفصيل فحص التشخيص"] = "كل أعمدة NCD وIMCI فارغة: نعم"
        errors = pd.concat([errors, frame], ignore_index=True, sort=False)
    if not errors.empty:
        errors = errors.drop_duplicates(subset=["اسم الملف", "رقم الصف الأصلي", "اسم قاعدة التدقيق"])
    return errors, skipped
