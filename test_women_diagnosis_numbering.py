import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine_womenfix2 import audit_dataframe
from utils.columns import detected_groups

def test_leading_and_trailing_numbered_columns_are_both_used():
    df=pd.DataFrame({
        "1الأمراض التوليدية":["تنظيم الأسرة","",""],
        "الأمراض التوليدية2":["","حمل",""],
        "1الأمراض النسائية":["","",""],
        "الأمراض النسائية3":["التهاب","",""],
    })
    ctx={"filename":"نساء.xlsx","clinic":"نسائية","mapping":{},"groups":detected_groups(df.columns),"settings":dict(DEFAULT_SETTINGS)}
    errors,_=audit_dataframe(df,ctx)
    missing=errors[errors["اسم قاعدة التدقيق"]=="غياب التشخيص"]
    assert list(missing["رقم الصف الأصلي"])==[4]
    assert "1الأمراض التوليدية" in missing.iloc[0]["الأعمدة المرتبطة بالخطأ"]
