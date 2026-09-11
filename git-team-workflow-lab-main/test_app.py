from app import project_summary, risk_level


def test_project_summary_contains_name_and_description():
    summary = project_summary()
    assert "Trailhead" in summary
    assert "team project planning tool" in summary


def test_risk_level_low_for_zero_blockers():
    assert risk_level(0) == "LOW"


def test_risk_level_medium_for_two_blockers():
    assert risk_level(2) == "MEDIUM"


def test_risk_level_high_for_four_blockers():
    assert risk_level(4) == "HIGH"
