import pandas as pd
from engine_rules import audit_dataframe as audit_existing
from utils.cleaning import clean_text,normalized
from validators.base import result_rows

RULE="غياب التشخيص"

def contains_family(column,family):
    name=normalized(column).replace("أ","ا").replace("إ","ا").replace("آ","ا")
    return family in name

def audit_dataframe(df,context):
    errors,skipped=audit_existing(df,context)
    if context["clinic"]!="نسائية": return errors,skipped
    if not errors.empty: errors=errors[errors["اسم قاعدة التدقيق"]!=RULE].copy()
    if not skipped.empty: skipped=skipped[skipped["اسم قاعدة التدقيق"]!=RULE].copy()

    # البحث داخل الاسم لا في بدايته فقط، لدعم 1الأمراض التوليدية والأمراض التوليدية1 و .1
    women=[c for c in df.columns if contains_family(c,"الامراض النسائية")]
    obstetric=[c for c in df.columns if contains_family(c,"الامراض التوليدية")]
    selected=context["groups"].get("gyne_indicators",[])
    women=list(dict.fromkeys(women+[c for c in selected if contains_family(c,"الامراض النسائية")]))
    obstetric=list(dict.fromkeys(obstetric+[c for c in selected if contains_family(c,"الامراض التوليدية")]))

    if not women or not obstetric:
        missing=[]
        if not women: missing.append("أعمدة الأمراض النسائية")
        if not obstetric: missing.append("أعمدة الأمراض التوليدية")
        skipped=pd.concat([skipped,pd.DataFrame([{"اسم الملف":context["filename"],"نوع العيادة":context["clinic"],"اسم قاعدة التدقيق":RULE,"سبب التجاوز":"لم يتم اكتشاف: "+"، ".join(missing)}])],ignore_index=True)
        return errors,skipped

    women_blank=~df[women].apply(lambda s:s.map(clean_text).ne("")).any(axis=1)
    obstetric_blank=~df[obstetric].apply(lambda s:s.map(clean_text).ne("")).any(axis=1)
    missing_diagnosis=women_blank & obstetric_blank
    columns=[*women,*obstetric]
    frame=result_rows(df,missing_diagnosis,context,RULE,
        "جميع أعمدة الأمراض النسائية فارغة وجميع أعمدة الأمراض التوليدية فارغة في السجل نفسه",
        columns)
    if not frame.empty:
        frame["تفصيل فحص التشخيص"]="النسائية فارغة: نعم | التوليدية فارغة: نعم"
        errors=pd.concat([errors,frame],ignore_index=True,sort=False)
    return errors,skipped
