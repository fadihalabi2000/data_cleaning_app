import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine_clinic_diagnosis import audit_dataframe
from utils.columns import detected_groups

def test_dressing_medicine_does_not_count_as_diagnosis():
    df=pd.DataFrame({"الضماد1":["","تنظيف"],"الضماد2":["",""],"أدوية الضماد":["مرهم","مرهم"]})
    ctx={"filename":"ضماد.xlsx","clinic":"ضماد","mapping":{},"groups":detected_groups(df.columns),"settings":dict(DEFAULT_SETTINGS)}
    errors,skipped=audit_dataframe(df,ctx)
    missing=errors[errors["اسم قاعدة التدقيق"]=="غياب التشخيص"]
    assert list(missing["رقم الصف الأصلي"])==[2]
    assert "أدوية الضماد" not in missing.iloc[0]["الأعمدة المرتبطة بالخطأ"]
    assert not any(skipped.get("اسم قاعدة التدقيق",pd.Series(dtype=str)).eq("غياب التشخيص"))
