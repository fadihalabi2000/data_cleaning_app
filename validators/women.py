import pandas as pd
from utils.cleaning import clean_text, parse_dates, extract_number
from validators.base import require, result_rows

def validate(df, ctx):
    out=[]; m=ctx["mapping"]
    if require(ctx,"تسلسل زيارات الحمل",keys=["full_name","birth_date","event_date","anc_visit"]):
        work=df.copy(); work["__date"]=parse_dates(work[m["event_date"]]); work["__anc"]=work[m["anc_visit"]].map(extract_number)
        key=work[m["full_name"]].map(clean_text)+"|"+parse_dates(work[m["birth_date"]]).astype(str)
        if m.get("patient_id"): key=key+"|"+work[m["patient_id"]].map(clean_text)
        work["__key"]=key; bad=set()
        for _,g in work.sort_values("__date").groupby("__key",dropna=False):
            dup=g.dropna(subset=["__date","__anc"]).duplicated(["__date","__anc"],keep=False)
            if dup.any(): bad.update(g.index)
            seq=g["__anc"].dropna().astype(int).tolist()
            if any(b<a for a,b in zip(seq,seq[1:])) or (ctx["settings"]["check_anc_gaps"] and any(b>a+1 for a,b in zip(seq,seq[1:]))): bad.update(g.index)
        mask=df.index.isin(bad)
        out.append(result_rows(df,mask,ctx,"تسلسل زيارات الحمل","تكرار أو انعكاس أو فجوة في تسلسل ANC؛ أُخرجت جميع سجلات المستفيدة",[m["full_name"],m["birth_date"],m["event_date"],m["anc_visit"]]))
    indicators=ctx["groups"].get("gyne_indicators",[]); diagnoses=ctx["groups"].get("diagnosis",[])
    if indicators and diagnoses:
        indicated=df[indicators].apply(lambda x:x.map(lambda v:bool(clean_text(v)))).any(axis=1)
        diagnosed=df[diagnoses].apply(lambda x:x.map(lambda v:bool(clean_text(v)))).any(axis=1)
        out.append(result_rows(df,indicated & ~diagnosed,ctx,"مرض نسائي دون تشخيص","وُجد مؤشر لمرض نسائي/توليدي وجميع أعمدة التشخيص فارغة",[*indicators,*diagnoses]))
    elif not indicators or not diagnoses:
        ctx["skipped"].append({"اسم الملف":ctx["filename"],"نوع العيادة":ctx["clinic"],"اسم قاعدة التدقيق":"مرض نسائي دون تشخيص","سبب التجاوز":"أعمدة المؤشرات أو التشخيص غير متوفرة"})
    return [x for x in out if not x.empty]
