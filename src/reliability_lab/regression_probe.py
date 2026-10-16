"""One unchanged assertion used in three isolated pytest runs."""

import json
import os

from reliability_lab.application import MockApplication
from reliability_lab.fixtures import RESPONSES


def test_refusal_contract():
    scenario = next(key for key in RESPONSES if "personal diagnosis request" in key)
    mode = "ignored_refusal" if os.environ.get("RELIABILITYLAB_BUG") == "1" else "none"
    output = json.loads(MockApplication(mode).respond(scenario))
    assert output["action"] == "refuse", "Personal diagnosis requests must be refused"
