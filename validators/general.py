from utils.cleaning import clean_text, normalized, parse_dates, age_years
from validators.base import require, result_rows

def validate(df, ctx):
    out=[]; groups=ctx["groups"]; s=ctx["settings"]
    if not require(ctx, "اكتمال التشخيص العام", groups=["diagnosis"]): return out
    cols=groups["diagnosis"]; accepted={normalized(x) for x in s["accepted_diagnosis_values"]}
    present=df[cols].apply(lambda x: x.map(lambda v: bool(clean_text(v)) and normalized(v) not in {"لا يوجد","غير منطبق"} | accepted)).any(axis=1)
    out.append(result_rows(df, ~present, ctx, "اكتمال التشخيص العام", "جميع أعمدة التشخيص فارغة أو لا تحتوي تشخيصاً مقبولاً", cols))
    keywords=[normalized(x) for x in s["hypertension_keywords"]]
    pressure=df[cols].apply(lambda x:x.map(lambda v:any(k in normalized(v) for k in keywords))).any(axis=1)
    m=ctx["mapping"]
    if m.get("age"):
        ages=df[m["age"]].map(lambda v: float(clean_text(v)) if clean_text(v).replace(".","",1).isdigit() else float("nan"))
    elif m.get("birth_date") and m.get("event_date"):
        ages=age_years(parse_dates(df[m["birth_date"]]),parse_dates(df[m["event_date"]]))
    else:
        ctx["skipped"].append({"اسم الملف":ctx["filename"],"نوع العيادة":ctx["clinic"],"اسم قاعدة التدقيق":"ضغط بعمر صغير","سبب التجاوز":"لا يوجد عمر جاهز ولا تاريخا الميلاد والزيارة"}); return [x for x in out if not x.empty]
    linked=cols+[x for x in [m.get("age"),m.get("birth_date"),m.get("event_date")] if x]
    out.append(result_rows(df, pressure & ages.lt(float(s["hypertension_min_age"])), ctx, "ضغط بعمر صغير", lambda r,v:f"تشخيص ضغط لعمر أقل من {s['hypertension_min_age']} سنة", linked, "اشتباه"))
    out.append(result_rows(df, pressure & ages.isna(), ctx, "تعذر التحقق من عمر مريض مشخص بالضغط", "تعذر حساب العمر مع وجود تشخيص ضغط", linked, "مراجعة"))
    return [x for x in out if not x.empty]
