from avg_rms_core.fake_adapter import FakeAdapter


def test_fake_adapter_success_is_byte_reproducible():
    adapter = FakeAdapter(mode="success")

    first = adapter.run_tool("fake.lookup", {"target": "alpha"})
    second = adapter.run_tool("fake.lookup", {"target": "alpha"})

    assert first.stdout == "FAKE_LOOKUP_OK target=alpha\n"
    assert second.stdout == "FAKE_LOOKUP_OK target=alpha\n"
    assert first.output_hash == second.output_hash
