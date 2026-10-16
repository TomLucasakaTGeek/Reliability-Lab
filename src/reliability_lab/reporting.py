"""Standalone local reports; embedded data is escaped before HTML insertion."""

import json
from pathlib import Path
from time import sleep


def save_snapshot(directory: Path, snapshot: dict) -> None:
    """Readers see either the previous complete snapshot or the new one."""
    pending = directory / "live.json.tmp"
    pending.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    # Windows readers can briefly hold a file without delete-sharing enabled.
    # Retry that transient conflict; persistent permission failures still surface.
    for attempt in range(20):
        try:
            pending.replace(directory / "live.json")
            break
        except PermissionError:
            if attempt == 19:
                raise
            sleep(0.01)


def save_reports(directory: Path, report: dict) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    template = Path(__file__).with_name("report_template.html").read_text(encoding="utf-8")
    safe = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    for name, contents in [("report.json", payload), ("report.html", template.replace("__REPORT_DATA__", safe))]:
        pending = directory / f"{name}.tmp"
        pending.write_text(contents, encoding="utf-8", newline="\n")
        pending.replace(directory / name)
