import pandas as pd
from validators import common, women, general, dressing, ncd, children

SPECIAL = {"نسائية": women, "عامة": general, "ضماد": dressing, "داخلية / NCD": ncd, "أطفال": children}

def audit_dataframe(df, context):
    context["skipped"] = []
    # العيادات التي لا تملك قواعد تخصصية (مثل المخاض حالياً) تستخدم القواعد المشتركة فقط.
    frames = common.validate(df, context)
    clinic_validator = SPECIAL.get(context["clinic"])
    if clinic_validator is not None:
        frames += clinic_validator.validate(df, context)
    errors = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    skipped = pd.DataFrame(context["skipped"])
    return errors, skipped
