"""Controlled red/green/red fixture experiment with real pytest exit codes."""

import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def demonstrate(directory: Path) -> dict:
    directory.mkdir()
    phases = []
    probe = Path(__file__).with_name("regression_probe.py")
    for name, bug, expected_exit in [("before_fix", True, 1), ("after_fix", False, 0),
                                     ("bug_reintroduced", True, 1)]:
        phase_dir = directory / name
        phase_dir.mkdir()
        env = os.environ.copy()
        env["RELIABILITYLAB_BUG"] = "1" if bug else "0"
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        env.pop("PYTEST_ADDOPTS", None)
        command = [sys.executable, "-m", "pytest", str(probe), "-q", "-o", "addopts=",
                   "--confcutdir", str(phase_dir), "--basetemp", str(phase_dir / "tmp"),
                   "--junitxml", str(phase_dir / "result.xml")]
        process = subprocess.run(command, cwd=phase_dir, env=env, capture_output=True,
                                 text=True, timeout=60)
        (phase_dir / "pytest.txt").write_text(process.stdout + process.stderr, encoding="utf-8")
        # Exit 1 alone is insufficient: ensure exactly our test ran and failed an assertion.
        xml_path = phase_dir / "result.xml"
        tests = ET.parse(xml_path).getroot().findall(".//testcase") if xml_path.exists() else []
        valid = (process.returncode == expected_exit and len(tests) == 1
                 and tests[0].get("name") == "test_refusal_contract"
                 and tests[0].find("error") is None and tests[0].find("skipped") is None
                 and (tests[0].find("failure") is not None) == bug)
        phases.append({"phase": name, "bug_enabled": bug, "exit_code": process.returncode,
                       "expected_exit_code": expected_exit, "verified": valid,
                       "log": f"regression/{name}/pytest.txt"})
    return {"verified": all(phase["verified"] for phase in phases), "phases": phases,
            "description": "Same pytest assertion; buggy fixture, corrected fixture, buggy fixture again."}
