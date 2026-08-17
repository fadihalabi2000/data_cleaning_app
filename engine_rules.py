import pandas as pd
from engine_v6 import audit_dataframe as audit_standard
from validators import custom_rules

def audit_dataframe(df, context):
    errors, skipped = audit_standard(df, context)
    context["skipped"] = skipped.to_dict("records") if not skipped.empty else []
    frames = custom_rules.validate(df, context)
    if frames:
        custom = pd.concat(frames, ignore_index=True, sort=False)
        errors = pd.concat([errors, custom], ignore_index=True, sort=False)
    if not errors.empty:
        errors = errors.drop_duplicates(subset=["اسم الملف","رقم الصف الأصلي","اسم قاعدة التدقيق"])
    return errors, pd.DataFrame(context["skipped"])
