# Build log

## 2026-10-16 — Interactive dashboard execution controls

Added baseline/demo buttons, custom case/fault selection, presentation-delay input, clickable pipeline stages and checks, Previous/Next trace navigation, and Follow live. Browser POST requests call the existing runner in a background thread. The API validates options, requires same-origin requests and a session token, and rejects duplicate dashboard jobs. No arbitrary commands or paths are accepted. No dependencies were added.

Browser verification launched custom `refuse_diagnosis` with `ignored_refusal`, observed one critical failure, and inspected expected `refuse` versus actual `answer` by clicking Five checks. Previous step changed the visible event from behavior to claims. A full-speed baseline exposed a Windows reader/replace collision in live snapshots; added bounded retries (persistent permission failures still raise) and regression tests. After the fix, the browser baseline completed **18/18 passing** and the browser demo completed **10 passing, 8 failing, 2 critical**, with verified pytest 1/0/1 outcomes.

Verification: `.venv/Scripts/python.exe -m pytest -q` with localhost access returned **132 passed in 5.53s**. `node --check` passed on the updated dashboard script. The live server is running on port 8765 with the updated controls. Prior failed diagnostic run artifacts are retained; subsequent verified runs are `18517a6d68de4ac9b8e2054d800fbdd8` (baseline) and `73535e9e89ca4b2a93a10c2aa9ac5d5d` (demo).

Known limitations: inspection pauses following, not execution; there is no execution pause/cancel control. Stopping the server can interrupt browser jobs. The dashboard uses the packaged synthetic dataset. Prepared for commit `Add interactive evaluation controls and trace navigation`.

## 2026-10-16 — Live command-following dashboard

Implemented the user's requested change from after-the-fact replay to live execution visibility. `watch --open` starts a read-only loopback server; independent `run`/`demo` commands publish atomic `live.json` snapshots at step start/end, case completion, and report persistence. The browser polls every 150 ms and follows the newest run, including partial checks and explicit running/completed/error states. Added optional 0–2 second presentation pacing outside measured computation. Static HTML reports remain available. No new dependencies; package version 0.3.0.

Verification: the sandbox blocked the test's localhost socket connection (WinError 10013). The same suite run with approved local network access passed **129 tests in 4.31s**. Tests prove the API exposes a running application before its future completes, completed snapshots match reports, newer runs are followed, invalid snapshots are ignored, file access is limited, timing excludes presentation pauses, and persistence failures remain visible. JavaScript passed `node --check`.

Packaging verification: built the 0.3.0 wheel, installed it without dependency changes in the separate verification environment, and ran the complete suite against that installation: **129 passed in 4.29s**. The live HTML template was served successfully by the installed package during the HTTP integration test.

Browser verification against `http://127.0.0.1:8765/` observed run `a4e413f662164755ae866eb80567f008` at **9/18** while its behavior check was running, then **18/18** completed with 8 intentional failures and the verified regression sequence. Selecting `refuse_diagnosis` showed the mismatched action and disabled following; re-enabling following worked. A screenshot was saved outside the repository in the output directory. The dashboard server was left running locally for the user.

Limitations: updates are polling, so sub-150ms stages may be skipped visually without pacing; all trace events remain recorded. Killed processes may leave stale snapshots, identified as stale rather than complete. This is a small local lab, not a multi-user server. No known failures remain in tested paths. Prepared for commit `Follow terminal evaluations in a live local dashboard`.

## 2026-10-16 — Core MVP, regression evidence, and visual explorer

Started with a clean working tree. Added a unified `python -m reliability_lab run|demo` entry point, per-step JSONL traces, unique run directories, JSON/HTML reports, sanitized exception recording, explicit exit codes, and a real pytest red/green/red regression experiment. The HTML report includes case search/filtering, a sequence diagram, recorded-step replay, actual durations, raw outputs, expectations, check evidence, and regression log links. It uses local assets only. Package data contains the dataset and HTML template; package version is 0.2.0.

Observed commands and results:

- Development `.venv/Scripts/python.exe -m pytest -q`: **125 passed in 4.68s**.
- Baseline `python -m reliability_lab run`: **18 passed, 0 failed, 0 critical**; artifacts saved under run `94cfc34f91dc4a35858af8b65886cfaa`.
- Final demo `python -m reliability_lab demo`: **10 passed, 8 failed, 2 critical**; regression exit sequence **1, 0, 1** verified against JUnit assertions. Final visual/JSON/trace artifacts exist under `runs/956f44c621e74ea191f78ffdefe31198/`.
- `pip wheel --no-deps --no-build-isolation`: built the package successfully. Installed that wheel plus its declared test extra into a separate, fresh venv using the global pip `--python` option. No unrelated packages were modified.
- From outside the repository, the fresh environment's `reliability-lab.exe run` and `demo` produced the same case outcomes; the imported package path was confirmed inside that environment's `site-packages`.
- The complete test suite against the installed wheel: **125 passed in 4.61s**. This verifies installation and packaged assets independently of the editable checkout.
- Extracted report JavaScript passed `node --check`, including the final UI text/stage update. Report escaping is covered by an automated test. `git diff --check` found no whitespace errors.

Browser validation limitation: the browser tool rejected local `file:` report URLs under its URL policy. No bypass was attempted. Visual layout and interactive controls therefore remain unverified in a real browser here; the user can open the saved report locally. The final UI-only change labels the saved-report stage and explains the filtered replay; core code is the version tested in the fresh environment.

Known implementation failures: none observed in the tested paths. Remaining limits: synchronous execution, exact fixtures and narrow deterministic checks, no live streaming/provider integration, and whole-run memory use. Reports intentionally store synthetic output/evidence, not real sensitive data. The regression is a controlled fixture bug/fix experiment, not a production incident claim.

Core required implementation work is complete. Next recommended user task: run `python -m reliability_lab demo --open`, inspect a failed case and its trace, and explain the three regression outcomes. A local browser review and interview understanding remain user-facing checks. Changes are prepared for commit `Complete traced evaluation MVP and visual run explorer`.

## 2026-10-16 — Milestone 3: independent deterministic evaluators

Started from a clean working tree. Added required version-two expectations and preserved the historical v1 dataset file. The active loader and preview now use schema 2.0. Added five separate checks (schema, required fields, disclaimer contract, prohibited phrases, expected behavior), explicit skipped results, case-level failure aggregation, and critical-failure counting. Added a terminal inspection command with exit codes 0/1/2. No dependencies added.

Verification: `.\.venv\Scripts\python.exe -m pytest -q` returned **112 passed in 1.40s** after final edits. Tests exercise every baseline, all injected output faults, duplicate JSON keys and nonstandard constants, missing expectations, evidence and summary behavior, and subprocess command exit codes including application exceptions and invalid dataset versions. `git diff --check` returned no issues.

Known limitations: exact comparisons and configured phrase matching, no arbitrary-prose factual verification, no saved run report or trace yet, and v1 datasets require migration to use the current loader. No failing tests observed. Next milestone: trace persistence, report files, and a controlled regression-cycle demonstration. Prepared for commit `Add deterministic evaluators and explicit dataset expectations`.

## 2026-10-16 — Milestone 2: deterministic mock application

Started from a clean Git working tree. Added an application protocol, explicit synthetic scenario fixtures, ten selectable modes (baseline plus nine failure modes), an output schema, and a single-case preview command. Expanded the version-one dataset to 18 cases across eight categories. The schema structure remains unchanged; Git preserves the old dataset and content hashing identifies the new snapshot. Added a Mermaid process map and runnable examples to the README.

Observed validation:

- `.\.venv\Scripts\python.exe -m pytest -q`: **64 passed in 0.32s**.
- `.\.venv\Scripts\python.exe -m reliability_lab.application --case valid_reference`: produced structured JSON with the expected blue booklet fact and all four fields.
- `.\.venv\Scripts\python.exe -m reliability_lab.application --case missing_summary --failure missing_field`: produced JSON with the summary deliberately omitted.

No dependencies added. No known failing tests. Limitations: exact scenario lookup, descriptive criteria not yet executed, and failure modes require appropriately selected scenarios. The preview is not an evaluation CLI and does not classify failures. Next task: independent evaluators and machine-readable expected behavior. Remaining work: evaluator milestone, tracing/reporting/runner milestone, and regression-cycle demonstration. This milestone is prepared for commit `Add deterministic mock application and 18 synthetic cases`.

## 2026-10-16 — Fix Windows pytest temporary-directory permissions

The user's test output showed 1 passed and 23 fixture setup errors: Windows denied access to the shared `Temp/pytest-of-14` directory. My earlier verification used an explicit workspace temporary path, but the published plain test command omitted it. Configured pytest to use the dedicated repository-local `.pytest-tmp/` directory by default, ignored it in Git, and documented its cleanup behavior. No test assertions were changed.

Verification: `.\.venv\Scripts\python.exe -m pytest -q` returned **24 passed in 0.23s**. Git was clean before this fix. Next milestone remains the deterministic application and expanded dataset.

## 2026-10-16 — Milestone 1: dataset loader

Completed: isolated Python package, strict version-one case schema, JSONL loader, dataset identification and SHA-256 hashing, useful aggregate errors, three synthetic examples, and pytest coverage.

Inspection: workspace contained only `outputs/` and `work/`, with no existing Git repository or project files. Python 3.14.6 was available; global Pydantic was 2.13.5 and pytest was absent. No global packages were upgraded.

Commands and observed results:

- `python -m venv outputs/reliability-lab/.venv`: environment created, but bundled `ensurepip` failed.
- `python -m pip --python outputs/reliability-lab/.venv/Scripts/python.exe install pip pytest 'pydantic>=2.13,<3' setuptools`: initially failed DNS resolution in the sandbox; approved retry succeeded in the isolated environment (Pydantic 2.14.1, pytest 9.1.1).
- Editable installation initially hit a sandbox temporary-directory permission error. Setting `TEMP` and `TMP` to the workspace `work/temp` directory resolved it.
- From the repository, `.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .`: successfully built and installed ReliabilityLab 0.1.0 using installed dependencies.
- `.\.venv\Scripts\python.exe -m pytest -q --basetemp ../../work/pytest-temp`: **24 passed in 0.34s**.

Known implementation bugs: none observed in tested behavior. Limitations: whole-file memory use, criteria lists remain mutable, no historical retrieval, no application/evaluation/tracing/CLI yet. Standard online clean setup instructions are provided but were not separately executed in a second environment.

Next recommended task: expand the dataset and implement deterministic fixture outputs. Estimated remaining work: approximately 3–4 focused 45-minute milestones, subject to debugging and learning time. No benchmark or production-readiness claims are made.

Git repository initialized locally. The milestone is staged for the commit `Build validated dataset loader with pytest coverage`; no remote is configured. `.gitattributes` preserves LF line endings across checkouts to avoid platform-only changes to the byte hash.

The installed-loader smoke command returned dataset `fictional-care-v1`, schema `1.0`, 3 cases, and hash `154fac8c50207dad3834d0c56353c05713e88fa45b4a57d3a778f685ed04699e`.
# Section 14 dashboard completion — 2026-10-16

Extended the existing dashboard without replacing its UI or adding dependencies. Added saved-run selection, Python-owned aggregation and artifact validation, evaluator bars, category filtering, two-run comparison, dataset-change explanations, and explicit history/invalid states. Case-stage status now reflects the selected case. Regression results link actual subprocess logs.

Validation: 137 tests passed. HTTP tests exercise history, selected artifacts, real comparisons, and missing-run errors. Browser verification created failure `07336ccb971e41a6815c85ba2934cf1b`, corrected run `06a1927f2a2d48fcbbc1de1620b5754a`, inspected behavior evidence, filtered cases, switched run metrics, and showed one recovery. CLI reintroduction `1beab7bc14cb40ce9e354bae41395e83` returned exit 1 with one critical failure. Core regression tests verify the unchanged pytest assertion fails, passes, then fails under controlled fixture switching.

`DEMO.md` records the single reproducible walkthrough and requirement map. These are synthetic fixtures, not real model calls or a claimed production fix. Stored run artifacts are not complete dataset snapshots. Earlier reports lacking completion metadata are labeled unknown and excluded from comparisons.

