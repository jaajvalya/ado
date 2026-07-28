from smoke_checks import smoke_ping


def test_smoke_ping():
    result = smoke_ping("sample_dev", "etl")
    assert result["ok"] is True
