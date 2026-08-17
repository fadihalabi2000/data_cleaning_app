import pandas as pd
from config.defaults import DEFAULT_SETTINGS
from engine_v4 import audit_dataframe
from utils.columns import auto_mapping, detected_groups

df = pd.DataFrame({
    "نوع الاستشارة ( هاتفية / فيزيائية )": ["هاتفية", "فيزيائية"],
    "تصوير": ["نعم", ""],
    "تشاخيص الضماد1": ["", "جرح"],
    "الضماد1": ["تنظيف", "تنظيف"],
})
mapping = auto_mapping(df.columns)
assert mapping["consultation_type"] == "نوع الاستشارة ( هاتفية / فيزيائية )"
assert mapping["imaging"] == "تصوير"
ctx = {"filename":"dressing.xlsx", "clinic":"ضماد", "mapping":mapping, "groups":detected_groups(df.columns), "settings":dict(DEFAULT_SETTINGS)}
errors, _ = audit_dataframe(df, ctx)
rules = set(errors["اسم قاعدة التدقيق"])
assert "استشارة هاتفية مع خدمة حضورية" in rules
assert "غياب التشخيص" in rules
assert len(errors[errors["اسم قاعدة التدقيق"] == "غياب التشخيص"]) == 1
print("OK v4:", sorted(rules))
