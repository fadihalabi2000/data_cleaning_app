import pandas as pd
from engine_v4 import audit_dataframe as audit_v4
from utils.cleaning import clean_text, normalized
from validators.base import result_rows

RULE = "استشارة هاتفية مع خدمة حضورية"

def audit_dataframe(df, context):
    errors, skipped = audit_v4(df, context)
    if not errors.empty:
        errors = errors[errors["اسم قاعدة التدقيق"] != RULE].copy()
    if not skipped.empty:
        skipped = skipped[skipped["اسم قاعدة التدقيق"] != RULE].copy()
    consultation = context["mapping"].get("consultation_type")
    services = list(dict.fromkeys(context["groups"].get("imaging", []) + context["groups"].get("labs", [])))
    if not consultation:
        skipped = pd.concat([skipped, pd.DataFrame([{"اسم الملف":context["filename"],"نوع العيادة":context["clinic"],"اسم قاعدة التدقيق":RULE,"سبب التجاوز":"لم يتم تحديد عمود نوع الاستشارة"}])], ignore_index=True)
        return errors, skipped
    if not services:
        skipped = pd.concat([skipped, pd.DataFrame([{"اسم الملف":context["filename"],"نوع العيادة":context["clinic"],"اسم قاعدة التدقيق":RULE,"سبب التجاوز":"لا توجد أعمدة تصوير أو مخبر"}])], ignore_index=True)
        return errors, skipped
    phone_values = {normalized(x) for x in context["settings"].get("phone_consultation_values", ["هاتفية"])}
    phone = df[consultation].map(normalized).isin(phone_values)
    service_used = df[services].apply(lambda s: s.map(clean_text).ne("")).any(axis=1)
    frame = result_rows(df, phone & service_used, context, RULE,
        "نوع الاستشارة هاتفية مع وجود قيمة في التصوير أو المخبر",
        [consultation, *services])
    if not frame.empty:
        errors = pd.concat([errors, frame], ignore_index=True, sort=False)
    return errors, skipped
