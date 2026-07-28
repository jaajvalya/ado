"""
QA regression helpers — data contract / row-count style checks.

Wire these into the QA stage after bundle deploy (DevOpsBase post-deploy
step, or a follow-on pipeline job). They are intentionally lightweight
placeholders to be replaced with real table/contract assertions.
"""

from __future__ import annotations


def assert_schema_columns(actual: list[str], expected: list[str]) -> None:
    missing = [c for c in expected if c not in actual]
    extra = [c for c in actual if c not in expected]
    if missing or extra:
        raise AssertionError(f"schema mismatch missing={missing} extra={extra}")


def assert_row_count_in_range(count: int, minimum: int, maximum: int) -> None:
    if count < minimum or count > maximum:
        raise AssertionError(
            f"row count {count} outside [{minimum}, {maximum}]"
        )
