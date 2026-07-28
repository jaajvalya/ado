# Contract this repo expects from DevOpsBase
# (databricks-asset-bundle-cicd-base.yaml + deploy template).
#
# DevOpsBase is external — confirm these behaviors with the DevOps team before
# go-live. If any item is false, do not treat CD as matching the adoption plan.

## Required behaviors

1. **No deploy on Pull Request**
   - This repo’s CD YAML has no `pr:` trigger.
   - If someone adds a PR trigger later, DevOpsBase must still no-op deploys when
     `Build.Reason` is `PullRequest` (or equivalent). Prefer keeping PR triggers off.

2. **Sequential stages: DEV → QA → PROD**
   - QA `dependsOn` successful DEV (including post-deploy smoke if provided).
   - PROD `dependsOn` successful QA (including regression if provided).
   - Dev and QA must **not** run in parallel for this project’s promotion model.
   - If the base template defaults to parallel Dev∥QA, enable a sequential mode
     parameter (wire it in `azure-pipelines-databricks-bundles.yml`) or provide
     a sequential template variant.

3. **Prod approval via ADO Environment**
   - Prod stage references `prodEnvironment`; approvers are configured on that
     Environment in ADO, not in git.

4. **Auth**
   - Per-env service connection obtains a Databricks token at runtime.
   - `DATABRICKS_HOST` and `BUNDLE_TARGET` come from the stage’s variable group.

5. **Idempotent, versioned deploys**
   - Redeploying a prior bundle/artifact version is the rollback mechanism
     (see `ROLLBACK.md`).

## Parameters this consumer sets

| Parameter | Purpose |
|---|---|
| `bundlePaths` | List of bundle directories to deploy |
| `deployDev` / `deployQa` / `deployProd` | Stage toggles |
| `nonProdPool` / `prodPool` | Agent pools |
| `variableGroupDev` / `Qa` / `Prod` | Per-env config |
| `azureServiceConnectionDev` / `Qa` / `Prod` | Per-env SPN auth |
| `prodEnvironment` | ADO Environment name for Prod approvals |
| sequential flag (if available) | Force DEV→QA→PROD ordering |

## Verification checklist (with DevOps)

- [ ] Template path `databricks-asset-bundle-cicd-base.yaml@DevOpsBase` resolves
- [ ] Sequential ordering confirmed in a test run (DEV finishes before QA starts)
- [ ] PR build of CD (if forced) does not deploy
- [ ] Variable group + service connection names match this org
- [ ] Rollback = re-run prior successful CD / redeploy prior bundle version
