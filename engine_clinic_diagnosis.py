from copy import deepcopy
from engine_womenfix2 import audit_dataframe as audit_existing
from utils.cleaning import normalized

def is_dressing_medicine(column):
    name=normalized(column).replace("أ","ا").replace("إ","ا").replace("آ","ا")
    return "ادوية" in name and "ضماد" in name

def audit_dataframe(df,context):
    # نسخة مستقلة من المجموعات حتى لا تنتقل إعدادات عيادة إلى أخرى.
    local=dict(context); local["groups"]=deepcopy(context["groups"])
    if context["clinic"]=="ضماد":
        dressing=[c for c in local["groups"].get("dressing",[]) if not is_dressing_medicine(c)]
        local["groups"]["dressing"]=dressing
        local["groups"]["diagnosis"]=dressing
    errors,skipped=audit_existing(df,local)
    if context["clinic"]=="ضماد" and not errors.empty:
        # القاعدة المشتركة «غياب التشخيص» تغني عن تقرير مكرر باسم بيانات الضماد مفقودة.
        errors=errors[errors["اسم قاعدة التدقيق"]!="بيانات الضماد مفقودة"].copy()
    return errors,skipped
