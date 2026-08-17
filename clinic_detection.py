from config.defaults import CLINIC_HINTS
from utils.cleaning import normalized


EXTRA_HINTS = {
    "أطفال": ["imci", "pediatric", "paediatric", "child", "اطفال", "أطفال"],
    "داخلية / NCD": ["ncd", "chronic", "داخلية"],
}


def weighted_suggest_clinic(filename, columns, program_values=()):
    filename_text = normalized(filename)
    column_text = normalized(" ".join(map(str, columns)))
    program_text = normalized(" ".join(map(str, program_values)))
    scores = {}
    for clinic, base_hints in CLINIC_HINTS.items():
        hints = {normalized(h) for h in [*base_hints, *EXTRA_HINTS.get(clinic, [])]}
        # اسم الملف ومرحلة البرنامج أكثر دلالة من وجود عمود مشترك مثل NCD.
        score = sum(8 for hint in hints if hint and hint in filename_text)
        score += sum(6 for hint in hints if hint and hint in program_text)
        score += sum(1 for hint in hints if hint and hint in column_text)
        scores[clinic] = score
    return max(scores, key=scores.get) if max(scores.values(), default=0) else "عامة"
