from validators.general import validate as diagnosis_validate
from validators.base import result_rows
from utils.cleaning import parse_dates, age_years

def validate(df, ctx):
    out=diagnosis_validate(df,ctx)
    m,s=ctx["mapping"],ctx["settings"]
    if s["check_pediatric_age"] and m.get("birth_date") and m.get("event_date"):
        ages=age_years(parse_dates(df[m["birth_date"]]),parse_dates(df[m["event_date"]]))
        x=result_rows(df, ages.ge(float(s["pediatric_max_age"])), ctx, "عمر مراجع عيادة الأطفال", lambda r,v:f"العمر يبلغ أو يتجاوز {s['pediatric_max_age']} سنة ويحتاج مراجعة", [m["birth_date"],m["event_date"]], "مراجعة")
        if not x.empty: out.append(x)
    return out
