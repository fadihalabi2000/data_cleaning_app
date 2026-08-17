import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine_v5 import audit_dataframe
from utils.columns import detected_groups

df=pd.DataFrame({
 "نوع الاستشارة ( هاتفية / فيزيائية )":["هاتفية","فيزيائية","هاتفية"],
 "تصوير":["نعم","نعم",""], "تشاخيص1":["جرح","جرح","جرح"], "الضماد1":["تنظيف"]*3})
ctx={"filename":"ضماد.xls","clinic":"ضماد","mapping":{"consultation_type":"نوع الاستشارة ( هاتفية / فيزيائية )"},"groups":detected_groups(df.columns),"settings":dict(DEFAULT_SETTINGS,phone_consultation_values=["هاتفية"])}
errors,skipped=audit_dataframe(df,ctx)
phone=errors[errors["اسم قاعدة التدقيق"]=="استشارة هاتفية مع خدمة حضورية"]
assert len(phone)==1 and phone.iloc[0]["رقم الصف الأصلي"]==2
assert not any(skipped.get("اسم قاعدة التدقيق",pd.Series(dtype=str)).eq("استشارة هاتفية مع خدمة حضورية"))
print("OK v5: phone errors=1, physical ignored")
