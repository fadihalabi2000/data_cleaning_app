import re
import pandas as pd

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

def clean_text(value):
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).translate(ARABIC_DIGITS)).strip()

def normalized(value):
    return clean_text(value).casefold().replace("ـ", "")

def is_blank(value):
    return clean_text(value) == ""

def has_meaningful_value(value, excluded=None):
    text = normalized(value)
    return bool(text) and text not in {normalized(x) for x in (excluded or [])}

def parse_dates(series):
    text = series.map(clean_text).replace("", pd.NA)
    return pd.to_datetime(text, errors="coerce", dayfirst=False)

def age_years(birth, event):
    return (event - birth).dt.total_seconds() / (365.2425 * 86400)

def extract_number(value):
    match = re.search(r"\d+", clean_text(value))
    return int(match.group()) if match else None
