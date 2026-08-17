from utils.cleaning import normalized

GENERAL_DIAGNOSIS_FAMILIES = (
    "ncd_not_applicable",
    "imci_not_applicable_up_5_year",
    "imci_applicable_from_2_to_59_month",
    "imci_applicable_under_2_month",
    "ncd",
)


def is_general_diagnosis(column):
    value = normalized(column).replace(" ", "_").replace("-", "_")
    if "drugs" in value:
        return False
    return any(family in value for family in GENERAL_DIAGNOSIS_FAMILIES)


def general_diagnosis_columns(columns):
    return [column for column in columns if is_general_diagnosis(column)]
