import pandas as pd
from validators import common, women, general, dressing, ncd, children, diagnosis_shared

SPECIAL = {"نسائية": women, "عامة": general, "ضماد": dressing, "داخلية / NCD": ncd, "أطفال": children}

def audit_dataframe(df, context):
    context["skipped"] = []
    frames = common.validate(df, context)
    clinic_validator = SPECIAL.get(context["clinic"])
    special_frames = clinic_validator.validate(df, context) if clinic_validator is not None else []
    frames += [frame for frame in special_frames if frame.empty or frame["اسم قاعدة التدقيق"].iloc[0] not in diagnosis_shared.SPECIAL_EMPTY_RULES]
    if context["clinic"] != "مخاض":
        frames += diagnosis_shared.validate(df, context)
    errors = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    if not errors.empty:
        errors = errors.drop_duplicates(subset=["اسم الملف", "رقم الصف الأصلي", "اسم قاعدة التدقيق"])
    return errors, pd.DataFrame(context["skipped"])
