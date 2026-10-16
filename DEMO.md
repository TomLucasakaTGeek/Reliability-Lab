# One clean investigation walkthrough

From the project folder, start the dashboard in one PowerShell terminal:

```powershell
.\.venv\Scripts\python.exe -m reliability_lab watch --open
```

Keep it open. In a second terminal, execute these commands one at a time, inspecting the dashboard between them. Both use the default `runs` output folder.

1. **Reproduce:**

   ```powershell
   .\.venv\Scripts\python.exe -m reliability_lab run --case refuse_diagnosis --failure ignored_refusal --step-delay 0.2
   ```

   Expected exit: **1**. Save the printed run ID as **Before**. Select `refuse_diagnosis` in the dashboard, then its behavior check. The trace shows expected action `refuse`, actual action `answer`, and measured elapsed time. Click the failure-category button to filter cases.

2. **Apply the controlled correction and rerun:**

   ```powershell
   .\.venv\Scripts\python.exe -m reliability_lab run --case refuse_diagnosis --failure none --step-delay 0.2
   ```

   Expected exit: **0**. Save this run ID as **After**. The fixture now returns `refuse`; the expected answer and evaluator remain unchanged. This is a controlled fixture correction, not a claim that we changed a production model or discovered a new code defect. The faulty branch is in `application.py`; the corrected response is in `fixtures.py`.

3. **Compare:** choose the two IDs in **Before** and **After**, then **Compare runs**. Expect one recovered case (`refuse_diagnosis`), zero newly failing cases, and matching dataset hashes. Use **Inspect run** to switch between the original failure and corrected result. Metrics and traces follow that selection. Choose **Live · newest run** to follow commands again.

4. **Reintroduce:** run the first command again. Compare the passing run against this new run: expect one newly failing case. Exit **1** confirms the unchanged evaluation checks still catch the fault.

5. **Verify the unchanged regression test:**

   ```powershell
   .\.venv\Scripts\python.exe -m reliability_lab demo
   ```

   This intentionally exits **1** for the seeded failures. Its regression panel links actual pytest logs: `before_fix` exits **1**, `after_fix` exits **0**, and `bug_reintroduced` exits **1**. The same assertion runs in all three subprocesses; JUnit results verify the cause of failure.

You can perform steps 1, 2, and 4 with **Run selection**, choosing `refuse_diagnosis` and switching the injected fault between `ignored_refusal` and `none`.

## Section 14 acceptance map

| Requirement | Implemented behavior and evidence |
|---|---|
| A: overview | Completed/pass/fail/critical counts; evaluator bars; clickable failure categories; run IDs, dataset hashes, saved-run selection. Aggregation validates stored summary counts against records. |
| B: trace explorer | Selected-case stage flow, actual span durations/status/errors/evidence, clickable failing checks, previous/next navigation. Running or unavailable timings are labeled; saving is not assigned an invented duration. |
| C: regression analysis | Two actual artifacts, recovered/newly failing/unchanged failures, added/removed/changed cases. Missing, invalid, incomplete, same-run comparisons are rejected. Recovery is observed behavior, not proof of causation. |
| D: datasets | Dataset ID/version label, schema version, exact-byte SHA-256; failed validation remains inspectable. Different hashes trigger a comparison warning. No complete dataset snapshot history is claimed. |
| E: interaction/states | Run selection, case/step selection, category filtering, comparison, live polling, loading/empty/error states. Invalid selection clears old results; interrupted runs are not treated as completed. |
| Architecture | Existing stdlib localhost server and HTML UI extended. Runner/models/traces/reporting remain independent. `run_analysis.py` owns aggregation, artifact loading, comparison; frontend renders their outputs. No new framework/database. |
| Integrity | Explicit synthetic fixtures, actual execution artifacts, no model-cost/token claims. `tests/test_run_analysis.py` checks real failure/correction/reintroduction, totals, invalid data, and changed/missing cases; HTTP integration checks the new endpoints. |

Run the entire test suite without manually launching the dashboard:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The HTTP integration tests start disposable local servers themselves. To run core tests without opening any server sockets:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_live.py
```

Historical artifacts from older versions without completion metadata are labeled `unknown` and excluded from comparison. The standalone HTML replay remains a single-run report; history/comparison live in the dashboard. Polling is every 150 ms, not a hard realtime guarantee; all recorded steps remain inspectable even when execution is faster than display refresh.
