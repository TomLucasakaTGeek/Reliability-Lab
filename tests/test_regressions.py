from pathlib import Path

from reliability_lab.regression import demonstrate


def test_same_assertion_catches_original_bug_after_fix(tmp_path):
    evidence = demonstrate(tmp_path / "regression")
    assert evidence["verified"]
    assert [phase["exit_code"] for phase in evidence["phases"]] == [1, 0, 1]
    for phase in evidence["phases"]:
        log = (tmp_path / phase["log"]).read_text()
        if phase["bug_enabled"]:
            assert "AssertionError" in log
            assert "1 failed" in log
        else:
            assert "1 passed" in log
