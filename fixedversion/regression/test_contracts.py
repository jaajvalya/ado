from contracts import assert_row_count_in_range, assert_schema_columns


def test_schema_contract_example():
    assert_schema_columns(
        actual=["id", "name", "updated_at"],
        expected=["id", "name", "updated_at"],
    )


def test_row_count_contract_example():
    assert_row_count_in_range(1000, minimum=1, maximum=1_000_000)
