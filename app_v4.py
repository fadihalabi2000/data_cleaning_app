import runpy
import config.defaults as defaults
import engine_pro
import engine_v4

# أسماء الأعمدة الفعلية الشائعة في تصدير DHIS2.
defaults.FIELD_ALIASES["consultation_type"] = [
    "نوع الاستشارة ( هاتفية / فيزيائية )",
    "نوع الاستشارة (هاتفية / فيزيائية)",
    "نوع الاستشارة هاتفية فيزيائية",
    "نوع الاستشارة",
]
defaults.FIELD_ALIASES["imaging"] = ["تصوير", "التصوير", "الأشعة", "Imaging"]

# تشغيل الواجهة الحالية بمحرك التدقيق المشترك الجديد.
engine_pro.audit_dataframe = engine_v4.audit_dataframe
runpy.run_path("app_v3.py", run_name="__main__")
