# Rollback

Rollback for Databricks Asset Bundle deploys in this project means **redeploying
a previously successful bundle version**, not manually undoing workspace edits.

## Prerequisites

- CD is idempotent (same bundle revision can be redeployed safely).
- Artifacts / git SHAs of successful Prod deploys are retained (pipeline run
  history + git tags or release records as your org prefers).

## Steps (typical)

1. Identify the last known-good git SHA or pipeline run that deployed to Prod.
2. Either:
   - Re-run that successful CD pipeline run’s Prod stage if ADO/DevOpsBase
     supports redeploy of an old run, **or**
   - Create a revert PR (or checkout the known-good SHA on a `hotfix/` branch),
     merge to `main` after PR CI, and let CD promote DEV → QA → PROD normally.
3. Confirm Prod smoke checks (`regression/smoke/`) after redeploy.
4. Record the incident / change work item with before/after SHAs.

## Do not

- Manually edit jobs in the Prod workspace UI as the primary rollback.
- Skip QA regression on a rollback unless the Prod approver documents an
  active-incident exception on the pipeline run.
