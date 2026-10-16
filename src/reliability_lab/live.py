"""Loopback dashboard with bounded, validated controls for synthetic evaluations."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import math
import secrets
from threading import Lock, Thread
from urllib.parse import parse_qs, unquote, urlsplit
import webbrowser

from reliability_lab.application import FailureMode
from reliability_lab.dataset import load_dataset
from reliability_lab.runner import run
from reliability_lab.run_analysis import aggregate, compare_runs, list_runs, read_run


def latest_snapshot(root: Path) -> dict | None:
    candidates = []
    for path in root.glob("*/live.json"):
        if not re.fullmatch(r"[0-9a-f]{32}", path.parent.name) or path.is_symlink() or path.parent.is_symlink():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("run_id") != path.parent.name or not isinstance(data.get("started_at"), str):
            continue
        candidates.append(data)
    return max(candidates, key=lambda data: data["started_at"], default=None)


def create_server(root: Path, port: int = 8765) -> ThreadingHTTPServer:
    if not 0 <= port <= 65535:
        raise ValueError("Invalid port")
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    dataset_path = Path(__file__).with_name("data") / "evaluation_cases.jsonl"
    cases = load_dataset(dataset_path).cases
    case_ids = {case.case_id for case in cases}
    token = secrets.token_urlsafe(32)
    job_lock = Lock()
    job = {"busy": False, "error": None}

    def execute(options: dict) -> None:
        try:
            run(dataset_path, root, case_id=options.get("case_id"),
                failure=options.get("failure", "none"), demo=options["mode"] == "demo",
                regression=options["mode"] == "demo", step_delay=options.get("step_delay", 0.2))
        except Exception as exc:
            job["error"] = f"Unable to finish run ({type(exc).__name__}); inspect output permissions."
        finally:
            job["busy"] = False
            job_lock.release()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            pass

        def send_json(self, status: int, value: dict) -> None:
            payload = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self) -> None:
            host = f"127.0.0.1:{self.server.server_port}"
            if (self.headers.get("Host") != host or self.headers.get("Origin") != f"http://{host}"
                    or not secrets.compare_digest(self.headers.get("X-Lab-Token", ""), token)):
                self.send_json(403, {"error": "Request must come from this dashboard."})
                return
            if self.path != "/api/run":
                self.send_json(404, {"error": "Unknown control."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096 or self.headers.get("Content-Type") != "application/json":
                    raise ValueError("Expected a small JSON request.")
                options = json.loads(self.rfile.read(length))
                if not isinstance(options, dict) or set(options) - {"mode", "case_id", "failure", "step_delay"}:
                    raise ValueError("Unknown run option.")
                if options.get("mode") not in {"baseline", "custom", "demo"}:
                    raise ValueError("Choose baseline, custom, or demo.")
                if options.get("case_id") is not None and options["case_id"] not in case_ids:
                    raise ValueError("Unknown case ID.")
                FailureMode(options.get("failure", "none"))
                delay = options.get("step_delay", 0.2)
                if type(delay) not in (int, float) or not math.isfinite(delay) or not 0 <= delay <= 2:
                    raise ValueError("Step delay must be between 0 and 2 seconds.")
                if options["mode"] in {"baseline", "demo"} and (options.get("case_id") is not None or options.get("failure", "none") != "none"):
                    raise ValueError("Use custom mode to choose cases or faults.")
            except (ValueError, TypeError):
                self.send_json(400, {"error": "Invalid run options. Select a listed case, fault, and delay from 0 to 2 seconds."})
                return
            if not job_lock.acquire(blocking=False):
                self.send_json(409, {"error": "A dashboard run is already in progress."})
                return
            job.update(busy=True, error=None)
            try:
                Thread(target=execute, args=(options,), daemon=True).start()
            except Exception:
                job["busy"] = False
                job_lock.release()
                self.send_json(500, {"error": "Unable to start evaluation."})
                return
            self.send_json(202, {"accepted": True})

        def do_GET(self) -> None:
            # Restrict Host to this server's loopback address; never expose arbitrary paths.
            expected = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != expected:
                self.send_error(403)
                return
            path = unquote(urlsplit(self.path).path)
            if path == "/":
                payload = Path(__file__).with_name("live_template.html").read_bytes()
                mime = "text/html; charset=utf-8"
            elif path == "/api/latest":
                snapshot = latest_snapshot(root)
                try:
                    if snapshot:
                        snapshot["overview"] = aggregate(snapshot)
                except (ValueError, KeyError, TypeError):
                    self.send_json(422, {"error": "Latest snapshot has invalid evaluation records."})
                    return
                payload = json.dumps({"run": snapshot, "control": job}).encode("utf-8")
                mime = "application/json"
            elif path == "/api/runs":
                self.send_json(200, {"runs": list_runs(root)})
                return
            elif path.startswith("/api/runs/") or path == "/api/compare":
                try:
                    if path == "/api/compare":
                        query = parse_qs(urlsplit(self.path).query)
                        value = compare_runs(read_run(root, query.get("before", [""])[0]),
                                             read_run(root, query.get("after", [""])[0]))
                    else:
                        value = {"run": read_run(root, path.removeprefix("/api/runs/"))}
                    self.send_json(200, value)
                except ValueError as exc:
                    self.send_json(422, {"error": str(exc)})
                return
            elif path == "/api/config":
                payload = json.dumps({"token": token, "cases": [{"case_id": c.case_id, "category": c.category} for c in cases],
                                      "failures": [mode.value for mode in FailureMode]}).encode("utf-8")
                mime = "application/json"
            elif path.startswith("/artifacts/"):
                parts = path.split("/")
                artifact = (len(parts) == 4 and parts[3] in {"report.html", "report.json", "traces.jsonl"})
                regression_log = (len(parts) == 6 and parts[3] == "regression"
                                  and parts[4] in {"before_fix", "after_fix", "bug_reintroduced"}
                                  and parts[5] in {"pytest.txt", "result.xml"})
                if len(parts) < 4 or not re.fullmatch(r"[0-9a-f]{32}", parts[2]) or not (artifact or regression_log):
                    self.send_error(404)
                    return
                target = root.joinpath(*parts[2:])
                if not target.is_file() or any(p.is_symlink() for p in [target, *target.parents] if p != root):
                    self.send_error(404)
                    return
                payload = target.read_bytes()
                mime = ("text/html; charset=utf-8" if target.suffix == ".html" else
                        "application/json" if target.suffix in {".json", ".jsonl"} else "text/plain; charset=utf-8")
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(root: Path, port: int, *, open_browser: bool = False) -> None:
    with create_server(root, port) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"Live dashboard: {url}\nWatching: {root.resolve()}\n"
              "Keep this terminal open. Start evaluations in the dashboard or another terminal. Ctrl+C stops the server.", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
