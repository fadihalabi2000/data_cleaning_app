import re
from config.defaults import CLINIC_HINTS, FIELD_ALIASES
from utils.cleaning import normalized

def normalize_column(name):
    return re.sub(r"\s+", " ", str(name)).strip()

def base_column(name):
    value = normalized(name)
    return re.sub(r"(?:[ ._-]?\d+)+$", "", value).strip(" ._-")

def find_column(columns, aliases):
    norm = {c: normalized(c) for c in columns}
    for alias in aliases:
        target = normalized(alias)
        exact = next((c for c, n in norm.items() if n == target), None)
        if exact is not None:
            return exact
    for alias in aliases:
        target = normalized(alias)
        fuzzy = next((c for c, n in norm.items() if target in n or n in target), None)
        if fuzzy is not None:
            return fuzzy
    return None

def auto_mapping(columns):
    return {key: find_column(columns, aliases) for key, aliases in FIELD_ALIASES.items()}

def find_group(columns, terms, starts=False, exclude=()):
    terms = [normalized(t) for t in terms]
    excluded = [normalized(t) for t in exclude]
    found = []
    for col in columns:
        n = normalized(col)
        b = base_column(col)
        if any(x in n for x in excluded):
            continue
        ok = any((b.startswith(t) or n.startswith(t)) if starts else (t in b or t in n) for t in terms)
        if ok:
            found.append(col)
    return found

def detected_groups(columns):
    return {
        "diagnosis": find_group(columns, ["تشاخيص", "تشخيص", "diagnosis"]),
        "labs": find_group(columns, ["المخبر", "مخبر", "laboratory", "lab"]),
        "imaging": find_group(columns, ["تصوير", "الأشعة", "imaging", "x-ray"]),
        "dressing": find_group(columns, ["الضماد", "ضماد", "dressing"]),
        "ncd": find_group(columns, ["ncd1", "ncd"], exclude=["not_applicable", "not applicable"]),
        "ncd_na": find_group(columns, ["ncd_not_applicable", "ncd not applicable"]),
        "gyne_indicators": find_group(columns, ["الأمراض النسائية", "الأمراض التوليدية"], starts=True),
    }

def suggest_clinic(filename, columns, program_values=()):
    haystack = normalized(" ".join([filename, *map(str, columns), *map(str, program_values)]))
    scores = {clinic: sum(normalized(h) in haystack for h in hints) for clinic, hints in CLINIC_HINTS.items()}
    return max(scores, key=scores.get) if max(scores.values(), default=0) else "عامة"
