import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine import audit_dataframe
from utils.columns import detected_groups

def context(df,clinic,mapping):
    return {"filename":"test.xlsx","clinic":clinic,"mapping":mapping,"groups":detected_groups(df.columns),"settings":dict(DEFAULT_SETTINGS)}

def rules(errors): return set(errors.get("اسم قاعدة التدقيق",[]))

def test_detects_numbered_and_duplicate_columns():
    groups=detected_groups(["تشاخيص1","تشاخيص 2","تشاخيص.1","NCD1","NCD1.1","NCD_Not_Applicable1.1"])
    assert len(groups["diagnosis"])==3 and len(groups["ncd"])==2 and len(groups["ncd_na"])==1

def test_hypertension_under_age():
    df=pd.DataFrame({"تشاخيص1":["ارتفاع ضغط الدم"],"العمر":[12]})
    e,_=audit_dataframe(df,context(df,"عامة",{"age":"العمر"}))
    assert "ضغط بعمر صغير" in rules(e)

def test_suture_without_injury():
    df=pd.DataFrame({"الضماد1":["خياطة جرح"],"نوع الإصابة":[""]})
    e,_=audit_dataframe(df,context(df,"ضماد",{"injury_type":"نوع الإصابة"}))
    assert "خياطة دون نوع إصابة" in rules(e)

def test_ncd_contradiction():
    df=pd.DataFrame({"NCD1":["سكري"],"NCD_Not_Applicable1":["نعم"]})
    e,_=audit_dataframe(df,context(df,"داخلية / NCD",{}))
    assert "تناقض تشخيص NCD" in rules(e)

def test_anc_gap_returns_all_patient_rows():
    df=pd.DataFrame({"الاسم الثلاثي":["سارة أحمد"]*2,"تاريخ الميلاد":["2000-01-01"]*2,"Event date":["2026-01-01","2026-02-01"],"رقم زيارة الحمل":["ANC1","ANC3"]})
    m={"full_name":"الاسم الثلاثي","birth_date":"تاريخ الميلاد","event_date":"Event date","anc_visit":"رقم زيارة الحمل"}
    e,_=audit_dataframe(df,context(df,"نسائية",m))
    assert len(e[e["اسم قاعدة التدقيق"]=="تسلسل زيارات الحمل"])==2
