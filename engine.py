import pandas as pd
from validators import common, women, general, dressing, ncd, pediatrics

SPECIAL = {"نسائية":women,"عامة":general,"ضماد":dressing,"داخلية / NCD":ncd,"أطفال":pediatrics}

def audit_dataframe(df, context):
    context["skipped"] = []
    frames = common.validate(df, context) + SPECIAL[context["clinic"]].validate(df, context)
    errors = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    skipped = pd.DataFrame(context["skipped"])
    return errors, skipped
