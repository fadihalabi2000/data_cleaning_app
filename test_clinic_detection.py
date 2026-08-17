from clinic_detection import weighted_suggest_clinic


def test_pediatric_filename_wins_over_shared_ncd_columns():
    columns = ["NCD1", "NCD_Not_Applicable1", "IMCI_APPLICABLE_UNDER_2_MONTH1"]
    assert weighted_suggest_clinic("Pediatric-7-2026.xls", columns) == "أطفال"


def test_program_stage_has_priority_over_shared_columns():
    columns = ["NCD1", "IMCI_APPLICABLE_FROM_2_TO_59_MONTH1"]
    assert weighted_suggest_clinic("export.xls", columns, ["عيادة الأطفال"]) == "أطفال"
