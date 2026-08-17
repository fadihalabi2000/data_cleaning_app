from copy import deepcopy

import pandas as pd

from child_diag_filter import child_diagnosis_columns
from engine_generalfix import audit_dataframe as audit_existing
from utils.cleaning import clean_text
from validators.base import result_rows


def audit_dataframe(df, context):
    if context["clinic"] != "أطفال":
        return audit_existing(df, context)

    local = dict(context)
    local["groups"] = deepcopy(context["groups"])
    detected = child_diagnosis_columns(df.columns)
    local["groups"]["diagnosis"] = detected or list(local["groups"].get("diagnosis", []))
    errors, skipped = audit_existing(df, local)

    replaced = {"غياب التشخيص", "اكتمال تشخيص الأطفال"}
    if not errors.empty:
        errors = errors[~errors["اسم قاعدة التدقيق"].isin(replaced)].copy()
    if not skipped.empty:
        skipped = skipped[~skipped["اسم قاعدة التدقيق"].isin(replaced)].copy()

    columns = local["groups"].get("diagnosis", [])
    if not columns:
        skipped = pd.concat([skipped, pd.DataFrame([{
            "اسم الملف": local["filename"],
            "نوع العيادة": "أطفال",
            "اسم قاعدة التدقيق": "غياب التشخيص",
            "سبب التجاوز": "لم يتم اكتشاف أعمدة IMCI الخمسة في الملف",
        }])], ignore_index=True)
        return errors, skipped

    # الخطأ فقط إذا كانت كل أعمدة IMCI فارغة معاً في الصف نفسه.
    all_blank = ~df[columns].apply(lambda series: series.map(clean_text).ne("")).any(axis=1)
    frame = result_rows(
        df, all_blank, local, "غياب التشخيص",
        "جميع أعمدة IMCI الخاصة بتشخيص الأطفال فارغة في السجل نفسه",
        columns,
    )
    if not frame.empty:
        frame["تفصيل فحص التشخيص"] = "كل أعمدة IMCI التشخيصية فارغة: نعم"
        errors = pd.concat([errors, frame], ignore_index=True, sort=False)
    if not errors.empty:
        errors = errors.drop_duplicates(subset=["اسم الملف", "رقم الصف الأصلي", "اسم قاعدة التدقيق"])
    return errors, skipped
