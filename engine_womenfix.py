import pandas as pd
from engine_rules import audit_dataframe as audit_existing
from utils.cleaning import clean_text
from validators.base import result_rows

RULE="غياب التشخيص"

def audit_dataframe(df,context):
    errors,skipped=audit_existing(df,context)
    if context["clinic"]!="نسائية":
        return errors,skipped
    if not errors.empty:
        errors=errors[errors["اسم قاعدة التدقيق"]!=RULE].copy()
    if not skipped.empty:
        skipped=skipped[skipped["اسم قاعدة التدقيق"]!=RULE].copy()
    # جميع أعمدة الأمراض النسائية والتوليدية، مع كل الترقيمات واللواحق.
    columns=list(dict.fromkeys(context["groups"].get("gyne_indicators",[])))
    if not columns:
        skipped=pd.concat([skipped,pd.DataFrame([{
            "اسم الملف":context["filename"],"نوع العيادة":context["clinic"],
            "اسم قاعدة التدقيق":RULE,
            "سبب التجاوز":"لم يتم اكتشاف أعمدة الأمراض النسائية أو الأمراض التوليدية",
        }])],ignore_index=True)
        return errors,skipped
    has_diagnosis=df[columns].apply(lambda series:series.map(clean_text).ne("")).any(axis=1)
    frame=result_rows(
        df,~has_diagnosis,context,RULE,
        "جميع أعمدة الأمراض النسائية وجميع أعمدة الأمراض التوليدية فارغة",
        columns,
    )
    if not frame.empty:
        errors=pd.concat([errors,frame],ignore_index=True,sort=False)
    return errors,skipped
