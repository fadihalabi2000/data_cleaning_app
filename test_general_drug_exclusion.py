from general_diag_filter import general_diagnosis_columns


def test_drug_columns_are_excluded_from_general_diagnosis():
    columns = [
        "IMCI_APPLICABLE_FROM_2_TO_59_MONTH_Drugs1",
        "IMCI_APPLICABLE_FROM_2_TO_59_MONTH_Drugs3",
        "NCD_Drugs4",
        "IMCI_APPLICABLE_FROM_2_TO_59_MONTH تشخيص 1",
        "NCD3",
    ]
    assert general_diagnosis_columns(columns) == columns[-2:]
