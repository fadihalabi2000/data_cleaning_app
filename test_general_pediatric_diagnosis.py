import pandas as pd
import pytest
from clinic_diagnosis_defaults import diagnosis_defaults
from config.defaults import DEFAULT_SETTINGS
from engine_clinic_diagnosis import audit_dataframe
from utils.columns import detected_groups

@pytest.mark.parametrize("clinic",["عامة","أطفال"])
def test_all_numbered_diagnosis_columns_are_combined(clinic):
    df=pd.DataFrame({
        "تشاخيص1":["التهاب","",""],
        "تشاخيص 2":["","سكري",""],
        "1تشاخيص":["","",""],
        "تشاخيص.3":["","",""],
        "تشخيص مفرد":["قيمة لا تدخل في المجموعة","", ""],
    })
    selected=diagnosis_defaults(df.columns)
    assert selected==["تشاخيص1","تشاخيص 2","1تشاخيص","تشاخيص.3"]
    groups=detected_groups(df.columns); groups["diagnosis"]=selected
    ctx={"filename":"test.xlsx","clinic":clinic,"mapping":{},"groups":groups,"settings":dict(DEFAULT_SETTINGS)}
    errors,_=audit_dataframe(df,ctx)
    missing=errors[errors["اسم قاعدة التدقيق"]=="غياب التشخيص"]
    assert list(missing["رقم الصف الأصلي"])==[4]
