import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine_rules import audit_dataframe
from utils.columns import detected_groups

df=pd.DataFrame({
 "نوع الزيارة":["جديد","مراجعة","جديد"],
 "المخبر1":["CBC","CBC",""],
 "العمر":[12,25,40],
 "تشاخيص1":["التهاب","التهاب","التهاب"],
})
rules=[{
 "name":"مخبر في زيارة جديدة","severity":"خطأ","logic":"all","message":"لا يسمح بالمخبر في الزيارة الجديدة",
 "conditions":[
   {"column":"نوع الزيارة","operator":"equals_any","values":["جديد"]},
   {"column":"المخبر1","operator":"not_blank"},
 ]
},{
 "name":"مراجعة عمرية","severity":"مراجعة","logic":"any","message":"العمر خارج المجال المرجعي",
 "conditions":[{"column":"العمر","operator":"less","number":14},{"column":"العمر","operator":"greater","number":35}]
}]
settings=dict(DEFAULT_SETTINGS); settings["custom_rules"]=rules
ctx={"filename":"custom.xlsx","clinic":"عامة","mapping":{"visit_type":"نوع الزيارة","age":"العمر"},"groups":detected_groups(df.columns),"settings":settings}
errors,_=audit_dataframe(df,ctx)
assert len(errors[errors["اسم قاعدة التدقيق"]=="مخبر في زيارة جديدة"])==1
assert len(errors[errors["اسم قاعدة التدقيق"]=="مراجعة عمرية"])==2
assert set(errors[errors["مصدر القاعدة"].eq("قاعدة مخصصة")]["رقم الصف الأصلي"])=={2,4}
print("OK custom rules: multi-column AND + numeric OR")
