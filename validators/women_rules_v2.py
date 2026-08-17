import re

import pandas as pd

from utils.cleaning import clean_text, normalized, parse_dates
from validators.base import result_rows
from validators.identity_utils import normalize_arabic_name


def canonical_pregnancy_type(value):
    text = normalized(value)
    if any(token in text for token in ("متعدد", "توأم", "توام", "multiple", "twin")):
        return "حمل متعدد"
    if any(token in text for token in ("مفرد", "single")):
        return "حمل مفرد"
    return clean_text(value)


def _patient_keys(df, mapping):
    patient_id = mapping.get("patient_id")
    name_col, birth_col = mapping.get("full_name"), mapping.get("birth_date")
    keys = []
    for _, row in df.iterrows():
        identifier = clean_text(row.get(patient_id, "")) if patient_id else ""
        if identifier:
            keys.append("id:" + identifier)
        elif name_col and birth_col:
            keys.append("name:" + normalize_arabic_name(row.get(name_col, "")) + "|" + clean_text(row.get(birth_col, "")))
        else:
            keys.append("")
    return pd.Series(keys, index=df.index)


def validate_pregnancy_type_consistency(df, ctx):
    mapping, settings = ctx["mapping"], ctx["settings"]
    pregnancy_col = settings.get("pregnancy_type_column") or mapping.get("pregnancy_type")
    if not pregnancy_col or pregnancy_col not in df.columns:
        return pd.DataFrame(), [{"اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "اسم قاعدة التدقيق": "ثبات نوع الحمل", "سبب التجاوز": "تعذر تشغيل قاعدة «ثبات نوع الحمل» لأن عمود نوع الحمل غير موجود أو لم يتم تحديده."}]
    keys = _patient_keys(df, mapping)
    if keys.eq("").all():
        return pd.DataFrame(), [{"اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "اسم قاعدة التدقيق": "ثبات نوع الحمل", "سبب التجاوز": "لا يوجد رقم مريض ولا الاسم الثلاثي مع تاريخ الميلاد لتجميع الزيارات."}]
    values = df[pregnancy_col].map(canonical_pregnancy_type)
    anc_col, event_col = mapping.get("anc_visit"), mapping.get("event_date")
    reasons, affected = {}, pd.Series(False, index=df.index)
    for key, indices in keys[keys.ne("")].groupby(keys).groups.items():
        distinct = [value for value in dict.fromkeys(values.loc[list(indices)]) if value]
        if len(distinct) <= 1:
            continue
        affected.loc[list(indices)] = True
        details = []
        ordered = list(indices)
        if event_col:
            ordered = list(parse_dates(df.loc[ordered, event_col]).sort_values().index)
        for idx in ordered:
            if values.loc[idx]:
                visit = clean_text(df.loc[idx, anc_col]) if anc_col else f"الصف {int(idx)+2}"
                details.append(f"{visit or f'الصف {int(idx)+2}'} = {values.loc[idx]}")
        reason = "يوجد اختلاف في نوع الحمل بين زيارات المستفيدة: " + "، ".join(details) + ". يرجى مراجعة واعتماد نوع الحمل الصحيح."
        for idx in indices:
            reasons[idx] = reason
    frame = result_rows(df, affected, ctx, "ثبات نوع الحمل", lambda row, values: reasons[row.name], [pregnancy_col, anc_col, event_col], "مراجعة")
    if not frame.empty:
        frame["تصنيف الملاحظة"] = "بحاجة للمراجعة"; frame["درجة الأهمية"] = "High"
    return frame, []


def is_anc_one(value):
    text = normalized(value).replace("-", " ")
    if "الزيارة الاولى" in normalize_arabic_name(text):
        return True
    compact = re.sub(r"\s+", "", text)
    return compact in {"1", "anc1"} or bool(re.fullmatch(r"anc\s*0*1", text))


def validate_anc1_not_phone(df, ctx):
    mapping = ctx["mapping"]
    anc_col, consultation_col = mapping.get("anc_visit"), mapping.get("consultation_type")
    if not anc_col or not consultation_col:
        missing = [label for value, label in [(anc_col, "رقم زيارة الحمل"), (consultation_col, "نوع الاستشارة")] if not value]
        return pd.DataFrame(), [{"اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "اسم قاعدة التدقيق": "ANC 1 مسجلة هاتفياً", "سبب التجاوز": "تعذر التشغيل لعدم تحديد: " + "، ".join(missing)}]
    phones = {normalized(value) for value in ctx["settings"].get("phone_consultation_values", [])}
    phones.update(normalized(value) for value in ["هاتفية", "هاتف", "Phone", "Telephone", "Teleconsultation"])
    phone_mask = df[consultation_col].map(normalized).map(lambda value: value in phones or any(token in value for token in phones if token))
    mask = df[anc_col].map(is_anc_one) & phone_mask
    frame = result_rows(df, mask, ctx, "ANC 1 مسجلة هاتفياً", "زيارة الحمل الأولى ANC 1 موثقة كاستشارة هاتفية، بينما الزيارة الأولى تتطلب مراجعة فيزيائية. يرجى مراجعة نوع الاستشارة.", [anc_col, consultation_col], "خطأ")
    if not frame.empty:
        frame["تصنيف الملاحظة"] = "خطأ"; frame["درجة الأهمية"] = "High"
    return frame, []


def run_women_rules(df, ctx):
    frames, skipped = [], []
    for validator in (validate_pregnancy_type_consistency, validate_anc1_not_phone):
        frame, missing = validator(df, ctx)
        if frame is not None and not frame.empty:
            frames.append(frame)
        skipped.extend(missing)
    return frames, skipped
