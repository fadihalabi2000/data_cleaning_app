import json
import pandas as pd
from utils.cleaning import clean_text

META_COLUMNS = ["اسم الملف", "نوع العيادة", "رقم الصف الأصلي", "Organisation unit name", "Program stage", "رقم تعريف المريض", "اسم قاعدة التدقيق", "درجة الحالة", "سبب الخطأ", "الأعمدة المرتبطة بالخطأ", "القيم المرتبطة بالخطأ"]

def skipped(rule, clinic, filename, missing):
    return {"اسم الملف": filename, "نوع العيادة": clinic, "اسم قاعدة التدقيق": rule, "سبب التجاوز": "أعمدة مفقودة: " + "، ".join(missing)}

def result_rows(df, mask, ctx, rule, reason, columns, severity="خطأ"):
    subset = df.loc[mask].copy()
    if subset.empty:
        return pd.DataFrame(columns=META_COLUMNS + list(df.columns))
    rows = []
    for idx, row in subset.iterrows():
        linked = [c for c in columns if c and c in df.columns]
        values = {str(c): clean_text(row[c]) for c in linked}
        record = {
            "اسم الملف": ctx["filename"], "نوع العيادة": ctx["clinic"], "رقم الصف الأصلي": int(idx) + 2,
            "Organisation unit name": clean_text(row.get(ctx["mapping"].get("org_unit"), "")),
            "Program stage": clean_text(row.get(ctx["mapping"].get("program_stage"), "")),
            "رقم تعريف المريض": clean_text(row.get(ctx["mapping"].get("patient_id"), "")),
            "اسم قاعدة التدقيق": rule, "درجة الحالة": severity,
            "سبب الخطأ": reason(row, values) if callable(reason) else reason,
            "الأعمدة المرتبطة بالخطأ": "، ".join(map(str, linked)),
            "القيم المرتبطة بالخطأ": json.dumps(values, ensure_ascii=False),
        }
        record.update({str(k): v for k, v in row.to_dict().items()})
        rows.append(record)
    return pd.DataFrame(rows).drop_duplicates(subset=["اسم الملف", "رقم الصف الأصلي", "اسم قاعدة التدقيق"])

def require(ctx, rule, keys=(), groups=()):
    missing = [k for k in keys if not ctx["mapping"].get(k)] + [g for g in groups if not ctx["groups"].get(g)]
    if missing:
        ctx["skipped"].append(skipped(rule, ctx["clinic"], ctx["filename"], missing))
        return False
    return True
