CLINIC_TYPES = ["نسائية", "عامة", "ضماد", "داخلية / NCD", "أطفال"]

FIELD_ALIASES = {
    "org_unit": ["Organisation unit name", "اسم المركز", "المركز الصحي"],
    "program_stage": ["Program stage", "العيادة", "مرحلة البرنامج"],
    "patient_id": ["رقم تعريف المريض", "Patient ID", "رقم المريض"],
    "full_name": ["الاسم الثلاثي", "اسم المريض", "Full name"],
    "birth_date": ["تاريخ الميلاد", "تاريخ التولد", "Date of birth"],
    "event_date": ["Event date", "تاريخ الزيارة"],
    "gender": ["الجنس", "Gender"],
    "residency": ["نوع الإقامة", "الإقامة"],
    "visit_type": ["نوع الزيارة"],
    "consultation_type": ["نوع الاستشارة"],
    "imaging": ["تصوير", "الأشعة"],
    "injury_type": ["نوع الإصابة"],
    "anc_visit": ["رقم زيارة الحمل", "ANC visit", "ANC"],
    "age": ["العمر", "Age"],
}

DEFAULT_SETTINGS = {
    "allowed_residency": ["مقيم", "نازح"],
    "max_age": 120.0,
    "hypertension_min_age": 18.0,
    "pediatric_max_age": 18.0,
    "hypertension_keywords": ["ضغط", "ارتفاع الضغط", "ارتفاع ضغط الدم", "hypertension", "htn"],
    "suture_keywords": ["خياطة", "خياطة جرح", "suturing", "suture"],
    "ncd_na_active_values": ["نعم", "yes", "true", "1", "غير منطبق"],
    "accepted_diagnosis_values": [],
    "check_anc_gaps": True,
    "check_empty_dressing": True,
    "check_pediatric_age": True,
}

CLINIC_HINTS = {
    "نسائية": ["نسائية", "women", "anc", "obstetric", "gyne"],
    "عامة": ["عامة", "general"],
    "ضماد": ["ضماد", "dressing", "wound"],
    "داخلية / NCD": ["داخلية", "ncd", "chronic"],
    "أطفال": ["أطفال", "اطفال", "pediatric", "child"],
}
