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
    default_types = result.get("درجة الحالة", "مراجعة").map({"خطأ": "خطأ", "اشتباه": "اشتباه", "مراجعة": "بحاجة للمراجعة"}).fillna("بحاجة للمراجعة")
    if "تصنيف الملاحظة" not in result:
        result["تصنيف الملاحظة"] = default_types
    else:
        result["تصنيف الملاحظة"] = result["تصنيف الملاحظة"].fillna(default_types).replace("", pd.NA).fillna(default_types)
    if "درجة الأهمية" not in result:
        result["درجة الأهمية"] = "Medium"
    for rule, (finding_type, importance) in RULE_METADATA.items():
        mask = result["اسم قاعدة التدقيق"].eq(rule)
        result.loc[mask & result["تصنيف الملاحظة"].isna(), "تصنيف الملاحظة"] = finding_type
        result.loc[mask & result["درجة الأهمية"].isna(), "درجة الأهمية"] = importance
        result.loc[mask & result["درجة الأهمية"].eq(""), "درجة الأهمية"] = importance
    result["درجة الأهمية"] = result["درجة الأهمية"].fillna("Medium")
    return result
