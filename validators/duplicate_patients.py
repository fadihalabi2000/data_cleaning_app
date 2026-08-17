from collections import defaultdict
from itertools import combinations

import pandas as pd

try:
    from rapidfuzz.fuzz import WRatio as name_ratio
except ImportError:
    from difflib import SequenceMatcher
    def name_ratio(left, right):
        return round(SequenceMatcher(None, left, right).ratio() * 100)

from utils.cleaning import clean_text, parse_dates
from validators.identity_utils import canonical_gender, normalize_arabic_name

RULE_NAME = "المستفيدون المحتمل تكرار تسجيلهم"


def _number(value):
    try:
        return float(clean_text(value))
    except (TypeError, ValueError):
        return None


def _date_score(days, maximum):
    if days is None:
        return 0.5
    if days <= 7:
        return 1.0
    if days <= 30:
        return 0.9
    if days <= maximum:
        return 0.75
    return 0.0


def _level(score):
    if score >= 90:
        return "اشتباه قوي جداً", "High"
    if score >= 80:
        return "اشتباه قوي", "High"
    return "بحاجة للمراجعة", "Medium"


def _candidate_pairs(df, names, genders, births, maximum_days):
    blocks = defaultdict(list)
    for idx in df.index:
        prefix = names.loc[idx].replace(" ", "")[:3]
        if not prefix:
            continue
        gender = genders.loc[idx] or "?"
        birth = births.loc[idx]
        year = int(birth.year) if pd.notna(birth) else None
        blocks[(prefix, gender, year)].append(idx)
    pairs = set()
    year_span = max(1, int(maximum_days // 365) + 1)
    keys = list(blocks)
    for prefix, gender, year in keys:
        candidates = []
        if year is None:
            candidates.extend(blocks[(prefix, gender, None)])
        else:
            for nearby in range(year - year_span, year + year_span + 1):
                candidates.extend(blocks.get((prefix, gender, nearby), []))
        for left in blocks[(prefix, gender, year)]:
            for right in candidates:
                if left < right:
                    pairs.add((left, right))
    return pairs


def validate_possible_duplicate_patients(df, ctx):
    mapping = ctx["mapping"]
    required = {"patient_id": "رقم تعريف المريض", "full_name": "الاسم الثلاثي"}
    missing = [label for key, label in required.items() if not mapping.get(key)]
    if missing:
        return pd.DataFrame(), [{"اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "اسم قاعدة التدقيق": RULE_NAME, "سبب التجاوز": "تعذر التشغيل لعدم تحديد: " + "، ".join(missing)}]
    id_col, name_col = mapping["patient_id"], mapping["full_name"]
    birth_col, residency_col, gender_col, age_col = (mapping.get(key) for key in ("birth_date", "residency", "gender", "age"))
    names = df[name_col].map(normalize_arabic_name)
    ids = df[id_col].map(clean_text)
    births = parse_dates(df[birth_col]) if birth_col else pd.Series(pd.NaT, index=df.index)
    genders = df[gender_col].map(canonical_gender) if gender_col else pd.Series("", index=df.index)
    residency = df[residency_col].map(normalize_arabic_name) if residency_col else pd.Series("", index=df.index)
    ages = df[age_col].map(_number) if age_col else pd.Series(None, index=df.index)
    maximum_days = int(ctx["settings"].get("duplicate_birthdate_max_days", 365))
    minimum_score = float(ctx["settings"].get("duplicate_min_score", 70))
    records = []
    for left, right in _candidate_pairs(df, names, genders, births, maximum_days):
        if not ids.loc[left] or not ids.loc[right] or ids.loc[left] == ids.loc[right]:
            continue
        name_score = float(name_ratio(names.loc[left], names.loc[right]))
        if name_score < 70:
            continue
        days = abs((births.loc[left] - births.loc[right]).days) if pd.notna(births.loc[left]) and pd.notna(births.loc[right]) else None
        if days is not None and days > maximum_days:
            continue
        gender_score = 1.0 if genders.loc[left] and genders.loc[left] == genders.loc[right] else (0.5 if not genders.loc[left] or not genders.loc[right] else 0.0)
        residency_score = 1.0 if residency.loc[left] and residency.loc[left] == residency.loc[right] else (0.5 if not residency.loc[left] or not residency.loc[right] else 0.0)
        age_left, age_right = ages.loc[left], ages.loc[right]
        age_score = 1.0 if age_left is None or age_right is None else max(0.0, 1.0 - abs(age_left - age_right) / 5.0)
        score = name_score * 0.50 + _date_score(days, maximum_days) * 25 + residency_score * 10 + gender_score * 10 + age_score * 5
        if score < minimum_score:
            continue
        level, importance = _level(score)
        reason = (
            f"{level} بوجود تسجيل مكرر لنفس المستفيد بكودين مختلفين. تشابه الاسم {name_score:.0f}%، "
            f"وفارق تاريخ الميلاد {days if days is not None else 'غير متاح'} يوم، ودرجة التشابه الإجمالية {score:.1f}%."
        )
        records.append({
            "اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "رقم الصف الأصلي": int(left) + 2,
            "رقم الصف الثاني": int(right) + 2, "Organisation unit name": clean_text(df.loc[left].get(mapping.get("org_unit"), "")),
            "Program stage": clean_text(df.loc[left].get(mapping.get("program_stage"), "")), "رقم تعريف المريض": ids.loc[left],
            "اسم قاعدة التدقيق": RULE_NAME, "درجة الحالة": "اشتباه", "تصنيف الملاحظة": "اشتباه", "درجة الأهمية": importance,
            "سبب الخطأ": reason, "Patient ID الأول": ids.loc[left], "Patient ID الثاني": ids.loc[right],
            "الاسم الأول": clean_text(df.loc[left, name_col]), "الاسم الثاني": clean_text(df.loc[right, name_col]),
            "تاريخ الميلاد الأول": clean_text(df.loc[left, birth_col]) if birth_col else "", "تاريخ الميلاد الثاني": clean_text(df.loc[right, birth_col]) if birth_col else "",
            "فرق تاريخ الميلاد بالأيام": days, "نوع الإقامة الأول": clean_text(df.loc[left, residency_col]) if residency_col else "",
            "نوع الإقامة الثاني": clean_text(df.loc[right, residency_col]) if residency_col else "", "الجنس الأول": clean_text(df.loc[left, gender_col]) if gender_col else "",
            "الجنس الثاني": clean_text(df.loc[right, gender_col]) if gender_col else "", "درجة تشابه الاسم": round(name_score, 1),
            "درجة التشابه الإجمالية": round(score, 1), "مستوى الاشتباه": level, "الأعمدة المرتبطة بالخطأ": "، ".join(filter(None, [id_col, name_col, birth_col, residency_col, gender_col])),
            "القيم المرتبطة بالخطأ": "",
        })
    return pd.DataFrame(records), []
