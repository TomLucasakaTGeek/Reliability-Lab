import json
from pathlib import Path
import pytest

from reliability_lab.reporting import save_reports
from reliability_lab.reporting import save_snapshot


def test_report_text_cannot_escape_embedded_json(tmp_path):
    malicious = '</script><script>alert("untrusted")</script>&'
    report = {"untrusted": malicious}
    save_reports(tmp_path, report)
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert malicious not in html
    embedded = html.split('<script id="report-data" type="application/json">')[1].split('</script>')[0]
    assert json.loads(embedded) == report
    assert json.loads((tmp_path / "report.json").read_text()) == report


def test_snapshot_retries_transient_windows_reader_lock(tmp_path, monkeypatch):
    original = Path.replace
    calls = []
    def locked_then_available(path, target):
        calls.append(target)
        if len(calls) < 3:
            raise PermissionError("reader still holds file")
        return original(path, target)
    monkeypatch.setattr(Path, "replace", locked_then_available)
    monkeypatch.setattr("reliability_lab.reporting.sleep", lambda seconds: None)
    save_snapshot(tmp_path, {"state": "running"})
    assert len(calls) == 3
    assert json.loads((tmp_path / "live.json").read_text()) == {"state": "running"}


def test_snapshot_persistent_permission_error_is_not_hidden(tmp_path, monkeypatch):
    def locked(path, target):
        raise PermissionError("permanent")
    monkeypatch.setattr(Path, "replace", locked)
    monkeypatch.setattr("reliability_lab.reporting.sleep", lambda seconds: None)
    with pytest.raises(PermissionError):
        save_snapshot(tmp_path, {})
