# Observed sample output

Actual baseline: 18 total, 18 passed, 0 failed, 0 critical failures.

Actual demo: 18 total, 10 passed, 8 failed, 2 critical failures; regression verified true.

Failure categories: MISSING_REQUIRED_FIELD=1, SCHEMA_INVALID=2, INVALID_JSON=1, PROHIBITED_CLAIM=1, EXPECTED_BEHAVIOR_MISMATCH=4. Categories overlap within cases.

Dataset SHA-256: 32402e080261f90d853d199b468c3da10e41efd9f120e84883b145a601828904.

Each command prints its unique run ID and actual artifact paths. Timings vary and are not benchmark claims. The demo exits 1 intentionally.
