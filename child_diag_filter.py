from utils.cleaning import normalized

CHILD_DIAGNOSIS_FAMILIES = (
    "imci_not_applicable_up_5_year",
    "imci_not_applicable_from_2_to_59_month",
    "imci_applicable_from_2_to_59_month",
    "imci_not_applicable_under_2_month",
    "imci_applicable_under_2_month",
)


def is_child_diagnosis(column):
    value = normalized(column).replace(" ", "_").replace("-", "_")
    if "drugs" in value:
        return False
    return any(family in value for family in CHILD_DIAGNOSIS_FAMILIES)


def child_diagnosis_columns(columns):
    return [column for column in columns if is_child_diagnosis(column)]
