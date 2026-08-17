import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine_womenfix import audit_dataframe
from utils.columns import detected_groups

def test_women_missing_requires_both_column_families_blank():
    df=pd.DataFrame({
        "الأمراض التوليدية1":["تنظيم الأسرة","",""],
        "الأمراض التوليدية 2":["","حامل", ""],
        "الأمراض النسائية1":["","",""],
        "الأمراض النسائية 2":["","التهاب", ""],
        "الأمراض النسائية3":["","",""],
    })
    ctx={"filename":"نساء.xlsx","clinic":"نسائية","mapping":{},"groups":detected_groups(df.columns),"settings":dict(DEFAULT_SETTINGS)}
    errors,_=audit_dataframe(df,ctx)
    missing=errors[errors["اسم قاعدة التدقيق"]=="غياب التشخيص"]
    assert list(missing["رقم الصف الأصلي"])==[4]
    linked=missing.iloc[0]["الأعمدة المرتبطة بالخطأ"]
    assert "الأمراض التوليدية1" in linked and "الأمراض النسائية3" in linked
