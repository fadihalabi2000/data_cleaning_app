"""قاعدة نسائية: تكرار زيارة ANC للمستفيدة نفسها في اليوم نفسه."""

import re

import pandas as pd

from utils.cleaning import clean_text, normalized, parse_dates
from validators.base import result_rows
from validators.identity_utils import normalize_arabic_name


RULE_NAME = "تكرار زيارة ANC في اليوم نفسه"

_ORDINALS = {
    "الاول": 1, "الاولى": 1,
    "الثاني": 2, "الثانية": 2,
    "الثالث": 3, "الثالثة": 3,
    "الرابع": 4, "الرابعة": 4,
    "الخامس": 5, "الخامسة": 5,
    "السادس": 6, "السادسة": 6,
    "السابع": 7, "السابعة": 7,
    "الثامن": 8, "الثامنة": 8,
}


def canonical_anc_visit(value):
    """توحيد ANC 1 وANC1 وANC-1 و1 والزيارة الأولى إلى قيمة واحدة."""
    text = normalize_arabic_name(normalized(value))
    if not text:
        return ""
    number = re.search(r"\d+", text)
    if number:
        return f"ANC {int(number.group())}"
    compact = re.sub(r"[^\w\u0600-\u06ff]+", "", text)
    for word, ordinal in _ORDINALS.items():
        if word in compact:
            return f"ANC {ordinal}"
    return compact


def _patient_keys(df, mapping):
    patient_id = mapping.get("patient_id")
    name_col = mapping.get("full_name")
    birth_col = mapping.get("birth_date")
    keys = []
    for _, row in df.iterrows():
        identifier = clean_text(row.get(patient_id, "")) if patient_id else ""
        if identifier:
            keys.append("id:" + identifier)
            continue
        name = normalize_arabic_name(row.get(name_col, "")) if name_col else ""
        birth = clean_text(row.get(birth_col, "")) if birth_col else ""
        keys.append(f"name:{name}|{birth}" if name and birth else "")
    return pd.Series(keys, index=df.index, dtype="object")


def validate_duplicate_anc_same_day(df, ctx):
    mapping = ctx.get("mapping", {})
    anc_col = mapping.get("anc_visit")
    event_col = mapping.get("event_date")
    missing = []
    if not anc_col or anc_col not in df.columns:
        missing.append("رقم زيارة الحمل ANC")
    if not event_col or event_col not in df.columns:
        missing.append("Event date")
    if missing:
        return pd.DataFrame(), [{
            "اسم الملف": ctx.get("filename", ""),
            "نوع العيادة": ctx.get("clinic", "نسائية"),
            "اسم قاعدة التدقيق": RULE_NAME,
            "سبب التجاوز": "تعذر التشغيل لعدم تحديد: " + "، ".join(missing),
        }]

    patients = _patient_keys(df, mapping)
    if patients.eq("").all():
        return pd.DataFrame(), [{
            "اسم الملف": ctx.get("filename", ""),
            "نوع العيادة": ctx.get("clinic", "نسائية"),
            "اسم قاعدة التدقيق": RULE_NAME,
            "سبب التجاوز": "تعذر تحديد المستفيدة: يلزم رقم تعريف المريض، أو الاسم الثلاثي مع تاريخ الميلاد.",
        }]

    visits = df[anc_col].map(canonical_anc_visit)
    dates = parse_dates(df[event_col]).dt.normalize()
    valid = patients.ne("") & visits.ne("") & dates.notna()
    keys = pd.DataFrame({"patient": patients, "visit": visits, "date": dates}, index=df.index)
    duplicated = pd.Series(False, index=df.index)
    reasons = {}

    for (patient, visit, event_date), indices in keys.loc[valid].groupby(
        ["patient", "visit", "date"], sort=False
    ).groups.items():
        rows = list(indices)
        if len(rows) < 2:
            continue
        duplicated.loc[rows] = True
        excel_rows = "، ".join(str(int(index) + 2) for index in rows)
        reason = (
            f"تم تسجيل {visit} للمستفيدة نفسها {len(rows)} مرات في اليوم "
            f"{pd.Timestamp(event_date).date()} (صفوف Excel: {excel_rows}). "
            "يرجى مراجعة السجلات وحذف التكرار غير الصحيح إن وجد."
        )
        for index in rows:
            reasons[index] = reason

    frame = result_rows(
        df,
        duplicated,
        ctx,
        RULE_NAME,
        lambda row, values: reasons[row.name],
        [mapping.get("patient_id"), mapping.get("full_name"), mapping.get("birth_date"), anc_col, event_col],
        "خطأ",
    )
    if not frame.empty:
        frame["تصنيف الملاحظة"] = "خطأ"
        frame["درجة الأهمية"] = "High"
        frame["زيارة ANC الموحدة"] = frame[anc_col].map(canonical_anc_visit)
        frame["تاريخ الزيارة الموحد"] = parse_dates(frame[event_col]).dt.date
    return frame, []


def install_women_rule(engine_module):
    """ربط القاعدة مرة واحدة بمحرك النسائية مع إبقاء القواعد الحالية."""
    if not hasattr(engine_module, "_anc_duplicate_base_run_women_rules"):
        engine_module._anc_duplicate_base_run_women_rules = engine_module.run_women_rules
    base = engine_module._anc_duplicate_base_run_women_rules

    def run_with_duplicate_anc(df, ctx):
        frames, skipped = base(df, ctx)
        frame, rule_skipped = validate_duplicate_anc_same_day(df, ctx)
        if frame is not None and not frame.empty:
            frames.append(frame)
        skipped.extend(rule_skipped)
        return frames, skipped

    engine_module.run_women_rules = run_with_duplicate_anc

