import os

import pytest


@pytest.mark.live
def test_live_provider_is_explicitly_opt_in() -> None:
    if os.environ.get("HFB_LIVE_TESTS") != "1":
        pytest.skip("set HFB_LIVE_TESTS=1 and a tiny explicit budget to enable live tests")
    pytest.fail(
        "Select and configure a provider-specific live fixture before enabling this marker."
    )
