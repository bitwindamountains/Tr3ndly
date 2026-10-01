from tr3ndly.db.models import DecisionType, SourceRunStatus


def test_workflow_enums_are_stable_strings() -> None:
    assert SourceRunStatus.SUCCEEDED.value == "succeeded"
    assert DecisionType.INSUFFICIENT_EVIDENCE.value == "insufficient_evidence"
