from filesense.categorizer import categorize_extension


def test_known_extension_is_categorized():
    assert categorize_extension(".pdf") == "Documents"


def test_extension_matching_is_case_insensitive():
    assert categorize_extension(".JPG") == "Images"


def test_unknown_extension_uses_other_category():
    assert categorize_extension(".madeup") == "Other"


def test_missing_extension_category():
    assert categorize_extension("[no extension]") == "Other"
