import pandas as pd


RULE_METADATA = {
    "رقم تعريف المريض مفقود": ("خطأ", "High"),
    "العمر السالب أو تاريخ الميلاد المستقبلي": ("خطأ", "High"),
    "عمر يتجاوز الحد المنطقي": ("خطأ", "High"),
    "ANC 1 مسجلة هاتفياً": ("خطأ", "High"),
    "ثبات نوع الحمل": ("بحاجة للمراجعة", "High"),
    "المستفيدون المحتمل تكرار تسجيلهم": ("اشتباه", "Medium"),
    "عدم تطابق الجنس": ("بحاجة للمراجعة", "Medium"),
    "تاريخ الميلاد غير صالح": ("خطأ", "High"),
    "تاريخ الزيارة غير صالح": ("خطأ", "High"),
    "غياب التشخيص": ("خطأ", "High"),
}


def enrich_findings(errors):
    if errors is None or errors.empty:
        return errors
    result = errors.copy()
    if "تصنيف الملاحظة" not in result:
        result["تصنيف الملاحظة"] = pd.NA
    if "درجة الأهمية" not in result:
        result["درجة الأهمية"] = pd.NA
    if "درجة الحالة" in result:
        defaults = result["درجة الحالة"].map(
            {"خطأ": "خطأ", "اشتباه": "اشتباه", "مراجعة": "بحاجة للمراجعة"}
        )
        result["تصنيف الملاحظة"] = result["تصنيف الملاحظة"].replace("", pd.NA).fillna(defaults)
    for rule, (finding_type, importance) in RULE_METADATA.items():
        mask = result["اسم قاعدة التدقيق"].eq(rule)
        result.loc[mask, "تصنيف الملاحظة"] = finding_type
        result.loc[mask, "درجة الأهمية"] = importance
    result["تصنيف الملاحظة"] = result["تصنيف الملاحظة"].fillna("بحاجة للمراجعة")
    result["درجة الأهمية"] = result["درجة الأهمية"].replace("", pd.NA).fillna("Medium")
    return result
