"""Pure transformation helpers for unit tests (no Spark required)."""


def normalize_column_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def row_count_delta(actual: int, expected: int) -> int:
    return actual - expected
