from validators.base import require, result_rows
from utils.cleaning import clean_text, normalized, parse_dates, age_years

def validate(df, ctx):
    out=[]
    if require(ctx,"اكتمال تشخيص الأطفال",groups=["diagnosis"]):
        cols=ctx["groups"]["diagnosis"]
        accepted={normalized(x) for x in ctx["settings"]["accepted_diagnosis_values"]}
        present=df[cols].apply(lambda x:x.map(lambda v:bool(clean_text(v)) and normalized(v) not in {"لا يوجد","غير منطبق"} | accepted)).any(axis=1)
        x=result_rows(df,~present,ctx,"اكتمال تشخيص الأطفال","جميع أعمدة تشخيص الأطفال فارغة أو لا تحتوي تشخيصاً مقبولاً",cols)
        if not x.empty: out.append(x)
    m,s=ctx["mapping"],ctx["settings"]
    if s["check_pediatric_age"] and m.get("birth_date") and m.get("event_date"):
        ages=age_years(parse_dates(df[m["birth_date"]]),parse_dates(df[m["event_date"]]))
        x=result_rows(df,ages.ge(float(s["pediatric_max_age"])),ctx,"عمر مراجع عيادة الأطفال",lambda r,v:f"العمر يبلغ أو يتجاوز {s['pediatric_max_age']} سنة ويحتاج مراجعة",[m["birth_date"],m["event_date"]],"مراجعة")
        if not x.empty: out.append(x)
    return out
