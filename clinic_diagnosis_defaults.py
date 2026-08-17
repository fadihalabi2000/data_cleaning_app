from utils.cleaning import normalized

def contains_diagnoses(column):
    return "تشاخيص" in normalized(column)

def diagnosis_defaults(columns):
    return [column for column in columns if contains_diagnoses(column)]
