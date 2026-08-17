import re

from utils.cleaning import clean_text

DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
NON_NAME = re.compile(r"[^\w\s\u0600-\u06FF]", re.UNICODE)


def normalize_arabic_name(value):
    text = clean_text(value)
    text = DIACRITICS.sub("", text).replace("ـ", "")
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    text = NON_NAME.sub(" ", text).casefold()
    return re.sub(r"\s+", " ", text).strip()


def normalized_first_name(value):
    text = normalize_arabic_name(value)
    return text.split()[0] if text else ""


def canonical_gender(value):
    text = normalize_arabic_name(value)
    if "انث" in text or text in {"f", "female"}:
        return "أنثى"
    if "ذكر" in text or text in {"m", "male"}:
        return "ذكر"
    return ""
