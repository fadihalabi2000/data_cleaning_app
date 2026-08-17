import pandas as pd

from utils.cleaning import age_years, parse_dates
from validators.base import result_rows
from validators.duplicate_patients import validate_possible_duplicate_patients
from validators.gender_rules import validate_gender_consistency


def validate_negative_or_future_age(df, ctx):
    mapping = ctx["mapping"]
    birth_col, event_col = mapping.get("birth_date"), mapping.get("event_date")
    if not birth_col or not event_col:
        missing = [label for value, label in [(birth_col, "تاريخ الميلاد"), (event_col, "Event date")] if not value]
        return pd.DataFrame(), [{"اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "اسم قاعدة التدقيق": "العمر السالب أو تاريخ الميلاد المستقبلي", "سبب التجاوز": "تعذر التشغيل لعدم تحديد: " + "، ".join(missing)}]
    births, events = parse_dates(df[birth_col]), parse_dates(df[event_col])
    ages = age_years(births, events)
    today = pd.Timestamp.today().normalize()
    invalid = births.gt(events) | births.gt(today) | ages.lt(0)
    frame = result_rows(
        df, invalid, ctx, "العمر السالب أو تاريخ الميلاد المستقبلي",
        lambda row, values: "تاريخ الميلاد يقع بعد تاريخ الزيارة أو في المستقبل، مما أدى إلى عمر سالب أو غير منطقي.",
        [birth_col, event_col], "خطأ",
    )
    if not frame.empty:
        frame["العمر المحسوب"] = frame["رقم الصف الأصلي"].map(lambda row: round(float(ages.iloc[int(row) - 2]), 2) if pd.notna(ages.iloc[int(row) - 2]) else None)
        frame["تصنيف الملاحظة"] = "خطأ"; frame["درجة الأهمية"] = "High"
    return frame, []


def validate_excessive_age(df, ctx):
    mapping = ctx["mapping"]
    birth_col, event_col = mapping.get("birth_date"), mapping.get("event_date")
    if not birth_col or not event_col:
        return pd.DataFrame(), []
    ages = age_years(parse_dates(df[birth_col]), parse_dates(df[event_col]))
    maximum = float(ctx["settings"].get("max_age", 100))
    frame = result_rows(df, ages.gt(maximum), ctx, "عمر يتجاوز الحد المنطقي", f"العمر المحسوب يتجاوز الحد الأعلى {maximum:g} سنة.", [birth_col, event_col], "خطأ")
    if not frame.empty:
        frame["تصنيف الملاحظة"] = "خطأ"; frame["درجة الأهمية"] = "High"
    return frame, []


def run_common_rules(df, ctx):
    frames, skipped = [], []
    for validator in (validate_negative_or_future_age, validate_excessive_age, validate_gender_consistency, validate_possible_duplicate_patients):
        frame, missing = validator(df, ctx)
        if frame is not None and not frame.empty:
            frames.append(frame)
        skipped.extend(missing)
    return frames, skipped
