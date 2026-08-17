from utils.cleaning import clean_text, normalized
from validators.base import result_rows

SPECIAL_EMPTY_RULES = {
    "اكتمال التشخيص العام",
    "اكتمال تشخيص الأطفال",
    "تشخيص NCD مفقود",
}

def diagnosis_columns(ctx):
    if ctx["clinic"] == "داخلية / NCD":
        return ctx["groups"].get("ncd", [])
    return ctx["groups"].get("diagnosis", [])

def validate(df, ctx):
    columns = diagnosis_columns(ctx)
    if not columns:
        ctx["skipped"].append({
            "اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"],
            "اسم قاعدة التدقيق": "غياب التشخيص",
            "سبب التجاوز": "لم يتم اكتشاف أو تحديد أي عمود تشخيص لهذه العيادة",
        })
        return []
    accepted = {normalized(x) for x in ctx["settings"].get("accepted_diagnosis_values", [])}
    invalid = {"لا يوجد", "غير منطبق", "لايوجد", "n/a", "na"}
    present = df[columns].apply(
        lambda series: series.map(lambda value: bool(clean_text(value)) and (normalized(value) in accepted or normalized(value) not in invalid))
    ).any(axis=1)
    result = result_rows(
        df, ~present, ctx, "غياب التشخيص",
        "جميع أعمدة التشخيص المحددة لهذه العيادة فارغة",
        columns,
    )
    return [result] if not result.empty else []
