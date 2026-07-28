from transforms import normalize_column_name, row_count_delta


def test_normalize_column_name():
    assert normalize_column_name(" Order Id ") == "order_id"


def test_row_count_delta():
    assert row_count_delta(100, 100) == 0
    assert row_count_delta(95, 100) == -5
