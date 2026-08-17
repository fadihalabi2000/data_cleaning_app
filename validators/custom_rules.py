import pandas as pd
from utils.cleaning import clean_text, normalized
from validators.base import result_rows

def condition_mask(df, condition):
    column, operator = condition["column"], condition["operator"]
    if column not in df.columns:
        return None
    raw = df[column]; text = raw.map(clean_text); norm = raw.map(normalized)
    values = condition.get("values", [])
    normalized_values = {normalized(v) for v in values}
    if operator == "is_blank": return text.eq("")
    if operator == "not_blank": return text.ne("")
    if operator == "equals_any": return norm.isin(normalized_values)
    if operator == "not_equals_any": return ~norm.isin(normalized_values)
    if operator == "contains_any": return norm.map(lambda value:any(token in value for token in normalized_values))
    if operator == "not_contains_any": return ~norm.map(lambda value:any(token in value for token in normalized_values))
    numeric = pd.to_numeric(text, errors="coerce")
    target = float(condition.get("number", 0))
    if operator == "greater": return numeric.gt(target)
    if operator == "greater_equal": return numeric.ge(target)
    if operator == "less": return numeric.lt(target)
    if operator == "less_equal": return numeric.le(target)
    if operator == "between": return numeric.between(float(condition.get("minimum",0)), float(condition.get("maximum",0)), inclusive="both")
    return pd.Series(False, index=df.index)

def validate(df, ctx):
    frames=[]
    for rule in ctx["settings"].get("custom_rules", []):
        masks=[]; missing=[]
        for condition in rule.get("conditions", []):
            mask=condition_mask(df,condition)
            if mask is None: missing.append(condition["column"])
            else: masks.append(mask)
        if missing:
            ctx["skipped"].append({"اسم الملف":ctx["filename"],"نوع العيادة":ctx["clinic"],"اسم قاعدة التدقيق":rule["name"],"سبب التجاوز":"أعمدة القاعدة المخصصة غير موجودة: "+"، ".join(missing)})
            continue
        if not masks: continue
        combined=masks[0]
        for mask in masks[1:]: combined = combined & mask if rule.get("logic","all")=="all" else combined | mask
        columns=list(dict.fromkeys(c["column"] for c in rule["conditions"]))
        reason=rule.get("message") or f"تحققت شروط القاعدة المخصصة «{rule['name']}»"
        frame=result_rows(df,combined,ctx,rule["name"],reason,columns,rule.get("severity","خطأ"))
        if not frame.empty:
            frame["مصدر القاعدة"]="قاعدة مخصصة"
            frames.append(frame)
    return frames
