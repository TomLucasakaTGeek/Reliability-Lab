from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from reliability_lab.application import MockApplication
from reliability_lab.live import create_server, latest_snapshot
from reliability_lab.runner import run
from reliability_lab.tracing import TraceWriter

DATA = Path(__file__).resolve().parents[1] / "datasets/v2/evaluation_cases.jsonl"


def test_dashboard_observes_running_case_before_command_finishes(tmp_path):
    entered, release = Event(), Event()

    class PausedApplication(MockApplication):
        def respond(self, scenario):
            entered.set()
            assert release.wait(10)
            return super().respond(scenario)

    server = create_server(tmp_path, 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        with ThreadPoolExecutor() as pool:
            future = pool.submit(run, DATA, tmp_path, application=PausedApplication(), case_id="valid_reference")
            try:
                assert entered.wait(10)
                with urlopen(url + "/api/latest") as response:
                    live = json.load(response)["run"]
                assert not future.done()
                assert live["state"] == "running"
                assert live["active"]["step"] == "application"
                assert live["active"]["case_id"] == "valid_reference"
                assert live["cases"][0]["passed"] is None
                assert not live["artifacts_saved"]
            finally:
                release.set()
            report, directory = future.result(timeout=10)
        with urlopen(url + "/api/latest") as response:
            completed = json.load(response)["run"]
        assert completed["state"] == "completed"
        assert completed["summary"]["passed_cases"] == 1
        assert completed["active"] is None
        assert completed["artifacts_saved"]
        with urlopen(url + f"/artifacts/{report['run_id']}/report.json") as response:
            assert json.load(response) == report
        with urlopen(url + "/") as response:
            assert b"Follow active case" in response.read()
        with urlopen(url + "/api/runs") as response:
            assert json.load(response)["runs"][0]["run_id"] == report["run_id"]
        with urlopen(url + "/api/runs/" + report["run_id"]) as response:
            assert json.load(response)["run"]["overview"]["summary"]["total_cases"] == 1
        failed, _ = run(DATA, tmp_path, case_id="valid_reference", failure="missing_field")
        with urlopen(url + f"/api/compare?before={failed['run_id']}&after={report['run_id']}") as response:
            assert json.load(response)["recovered"] == ["valid_reference"]
        with pytest.raises(HTTPError) as caught:
            urlopen(url + "/api/compare?before=missing&after=missing")
        assert caught.value.code == 422
        for path in ["/artifacts/../README.md", "/artifacts/" + report["run_id"] + "/live.json"]:
            with pytest.raises(HTTPError) as caught:
                urlopen(url + path)
            assert caught.value.code == 404
        with pytest.raises(HTTPError) as caught:
            urlopen(Request(url + "/api/latest", headers={"Host": "untrusted.example"}))
        assert caught.value.code == 403
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join()


def test_dashboard_follows_subsequent_run_and_ignores_invalid_snapshot(tmp_path):
    assert latest_snapshot(tmp_path) is None
    first, _ = run(DATA, tmp_path, case_id="valid_reference")
    second, _ = run(DATA, tmp_path, case_id="missing_summary", failure="missing_field")
    assert latest_snapshot(tmp_path)["run_id"] == second["run_id"] != first["run_id"]
    bad = tmp_path / ("f" * 32)
    bad.mkdir()
    (bad / "live.json").write_text("{partial")
    assert latest_snapshot(tmp_path)["run_id"] == second["run_id"]


def test_presentation_pause_is_outside_measured_duration(tmp_path, monkeypatch):
    calls = []
    clock = iter([100.0, 100.025])
    monkeypatch.setattr("reliability_lab.tracing.sleep", lambda delay: calls.append(("sleep", delay)))
    monkeypatch.setattr("reliability_lab.tracing.perf_counter", lambda: next(clock))
    def observe(active):
        calls.append(("update", "running" if active else "finished"))
    trace = TraceWriter(tmp_path / "trace.jsonl", "run", "mock", on_update=observe, step_delay=0.2)
    with trace.step("application"):
        calls.append(("execute", None))
    assert calls == [("update", "running"), ("sleep", 0.2), ("execute", None), ("update", "finished")]
    assert trace.events[0]["duration_ms"] == pytest.approx(25)


def test_report_save_failure_is_visible_live(tmp_path, monkeypatch):
    def broken(*args):
        raise OSError("cannot write")
    monkeypatch.setattr("reliability_lab.runner.save_reports", broken)
    with pytest.raises(OSError):
        run(DATA, tmp_path, case_id="valid_reference")
    live = latest_snapshot(tmp_path)
    assert live["state"] == "error"
    assert live["exit_code"] == 2
    assert not live["artifacts_saved"]


def test_dashboard_controls_launch_real_run_and_reject_unsafe_requests(tmp_path):
    server = create_server(tmp_path, 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(url + "/api/config") as response:
            config = json.load(response)
        assert len(config["cases"]) == 18
        def post(options, origin=url, token=config["token"]):
            request = Request(url + "/api/run", data=json.dumps(options).encode(),
                              headers={"Content-Type": "application/json", "Origin": origin,
                                       "X-Lab-Token": token}, method="POST")
            return urlopen(request)
        options = {"mode": "custom", "case_id": "missing_summary", "failure": "missing_field", "step_delay": 0.1}
        for origin, token in [("http://untrusted.example", config["token"]), (url, "invalid")]:
            with pytest.raises(HTTPError) as caught:
                post(options, origin=origin, token=token)
            assert caught.value.code == 403
        for invalid in [dict(options, command="anything"), dict(options, step_delay=-1),
                        dict(options, case_id="unknown"), dict(options, mode="demo"),
                        dict(options, failure="unknown"), dict(options, step_delay=float("nan"))]:
            with pytest.raises(HTTPError) as caught:
                post(invalid)
            assert caught.value.code == 400
        with post(options) as response:
            assert response.status == 202
        with pytest.raises(HTTPError) as caught:
            post(options)
        assert caught.value.code == 409
        deadline = monotonic() + 10
        while monotonic() < deadline:
            with urlopen(url + "/api/latest") as response:
                state = json.load(response)
            if not state["control"]["busy"]:
                break
            sleep(0.05)
        assert not state["control"]["busy"]
        assert state["control"]["error"] is None
        assert state["run"]["summary"]["failed_cases"] == 1
        assert state["run"]["cases"][0]["case_id"] == "missing_summary"
        assert state["run"]["artifacts_saved"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
