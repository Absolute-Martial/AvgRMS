from avg_rms_core.fake_adapter import FakeAdapter


def test_fake_adapter_success_is_byte_reproducible():
    adapter = FakeAdapter(mode="success")

    first = adapter.run_tool("fake.lookup", {"target": "alpha"})
    second = adapter.run_tool("fake.lookup", {"target": "alpha"})

    assert first.stdout == "FAKE_LOOKUP_OK target=alpha\n"
    assert second.stdout == "FAKE_LOOKUP_OK target=alpha\n"
    assert first.output_hash == second.output_hash


def test_fake_adapter_fails_once_then_succeeds():
    adapter = FakeAdapter(mode="fail_once")

    first = adapter.run_tool("fake.lookup", {"target": "alpha"})
    second = adapter.run_tool("fake.lookup", {"target": "alpha", "retry": 1})

    assert first.status == "error"
    assert first.error == "simulated runtime error"
    assert second.status == "ok"


def test_fake_adapter_always_fail_mode_is_deterministic():
    adapter = FakeAdapter(mode="always_fail")

    result = adapter.run_tool("fake.lookup", {"target": "alpha"})

    assert result.status == "error"
    assert result.stdout == "FAKE_LOOKUP_ERROR target=alpha\n"
