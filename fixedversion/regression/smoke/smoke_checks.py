"""
Post-deploy smoke checks (DEV / PROD).

Replace `ping` with real workspace/job health checks (e.g. list job run,
query a known health view). Keep these fast — not a full regression suite.
"""


def smoke_ping(catalog: str, schema: str) -> dict:
    return {"ok": True, "catalog": catalog, "schema": schema}
