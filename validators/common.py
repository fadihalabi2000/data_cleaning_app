import pandas as pd
from utils.cleaning import clean_text, normalized, parse_dates, age_years
from validators.base import require, result_rows

def validate(df, ctx):
    out, m, s = [], ctx["mapping"], ctx["settings"]
    if require(ctx, "نوع الإقامة", keys=["residency"]):
        c = m["residency"]; allowed = {normalized(x) for x in s["allowed_residency"]}
        out.append(result_rows(df, ~df[c].map(normalized).isin(allowed), ctx, "نوع الإقامة", lambda r,v: f"قيمة الإقامة «{clean_text(r[c])}» غير مسموحة؛ المسموح: {', '.join(s['allowed_residency'])}", [c]))
    if require(ctx, "نوع الزيارة مفقود", keys=["visit_type"]):
        c=m["visit_type"]; out.append(result_rows(df, df[c].map(clean_text).eq(""), ctx, "نوع الزيارة مفقود", "نوع الزيارة فارغ", [c]))
    if require(ctx, "رقم تعريف المريض مفقود", keys=["patient_id"]):
        c=m["patient_id"]; out.append(result_rows(df, df[c].map(clean_text).eq(""), ctx, "رقم تعريف المريض مفقود", "رقم تعريف المريض فارغ", [c]))
    linked = list(dict.fromkeys(ctx["groups"].get("imaging", []) + ctx["groups"].get("labs", [])))
    if require(ctx, "استشارة هاتفية مع خدمة حضورية", keys=["consultation_type"], groups=[]):
        if linked:
            c=m["consultation_type"]; phone=df[c].map(normalized).eq(normalized("هاتفية")); used=df[linked].apply(lambda x: x.map(clean_text).ne("")).any(axis=1)
            out.append(result_rows(df, phone & used, ctx, "استشارة هاتفية مع خدمة حضورية", "استشارة هاتفية مسجل معها تصوير أو مخبر", [c,*linked]))
        else: ctx["skipped"].append({"اسم الملف":ctx["filename"],"نوع العيادة":ctx["clinic"],"اسم قاعدة التدقيق":"استشارة هاتفية مع خدمة حضورية","سبب التجاوز":"لا توجد أعمدة تصوير أو مخبر"})
    if require(ctx, "سلامة تاريخ الميلاد", keys=["birth_date"]):
        c=m["birth_date"]; parsed=parse_dates(df[c]); raw=df[c].map(clean_text).ne("")
        out.append(result_rows(df, raw & parsed.isna(), ctx, "تاريخ الميلاد غير صالح", "تعذر تحويل تاريخ الميلاد", [c]))
    if require(ctx, "سلامة تاريخ الزيارة", keys=["event_date"]):
        c=m["event_date"]; parsed=parse_dates(df[c]); raw=df[c].map(clean_text).ne("")
        out.append(result_rows(df, raw & parsed.isna(), ctx, "تاريخ الزيارة غير صالح", "تعذر تحويل تاريخ الزيارة", [c]))
    if m.get("birth_date") and m.get("event_date"):
        b,e=parse_dates(df[m["birth_date"]]),parse_dates(df[m["event_date"]]); ages=age_years(b,e)
        out.append(result_rows(df, ages.lt(0), ctx, "عمر سالب", "تاريخ الميلاد بعد تاريخ الزيارة", [m["birth_date"],m["event_date"]]))
        out.append(result_rows(df, ages.gt(float(s["max_age"])), ctx, "عمر غير منطقي", lambda r,v: f"العمر المحسوب يتجاوز الحد الأعلى {s['max_age']} سنة", [m["birth_date"],m["event_date"]]))
    return [x for x in out if not x.empty]
