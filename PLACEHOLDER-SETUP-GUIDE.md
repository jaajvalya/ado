# Placeholder Setup Guide

This guide covers every placeholder left in [`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml) and [`bundles/sample_data_pipeline/`](bundles/sample_data_pipeline/): what it is, exactly where to change it, who to get the value from, and how to confirm it's correct before the pipeline runs for real.

Work through this top to bottom — later items (variable groups, service connections) depend on earlier ones (which Databricks workspaces/environments exist) being settled first.

---

## Quick reference table

| # | Placeholder | File / line | Get it from |
|---|---|---|---|
| 1 | DevOpsBase repo path | `azure-pipelines-databricks-bundles.yml:36` | DevOps team |
| 2 | Agent pools (non-prod/prod) | `azure-pipelines-databricks-bundles.yml:51-52` | DevOps team / ADO org settings |
| 3 | Variable groups (dev/qa/prod) | `azure-pipelines-databricks-bundles.yml:53-55` | DevOps team + Databricks workspace admin |
| 4 | Service connections (dev/qa/prod) | `azure-pipelines-databricks-bundles.yml:56-58` | DevOps team / Azure AD (Entra ID) admin |
| 5 | Prod environment name + approvals | `azure-pipelines-databricks-bundles.yml:59` | DevOps team + your engineering lead |
| 6 | Real bundle paths | `azure-pipelines-databricks-bundles.yml:46` | You (this project's actual pipelines) |

---

## 1. DevOpsBase repository path

**Where:** `azure-pipelines-databricks-bundles.yml:36`
```yaml
name: "<AZURE_DEVOPS_PROJECT>/DevOpsBase" # TODO: replace with actual project/repo path
```

**What it needs to become:** `"<ADO Project Name>/DevOpsBase"` — the Azure DevOps **project** that contains the `DevOpsBase` repo (same format as the example in their docs, `"Rheem EDP/DevOpsBase"`, just with your org's project name).

**Where to get it:**
- Ask the DevOps team which ADO **project** hosts `DevOpsBase`, or
- If you have ADO access yourself: go to `https://dev.azure.com/<your-org>` → browse projects → find the one containing a `DevOpsBase` repo → the path is `<Project Name>/DevOpsBase`.

**How to verify:** Once set, queue the pipeline (or just save it in the ADO pipeline editor) — if the path/permissions are wrong, ADO will fail at parse time with a "could not find repository" or "template not found" error, before any stage runs.

**Also required:** This repo's pipeline needs **permission to use** the DevOpsBase repository resource. If you get a permission error even with the correct path, ask the DevOps team to authorize this pipeline (or the whole project) against `DevOpsBase`.

---

## 2. Agent pools

**Where:** `azure-pipelines-databricks-bundles.yml:51-52`
```yaml
# nonProdPool: <NONPROD_AGENT_POOL>
# prodPool: <PROD_AGENT_POOL>
```

**What it needs to become:** The names of existing Azure DevOps **agent pools** (self-hosted or Microsoft-hosted) that this pipeline is allowed to run on — one for Dev/QA, one for Prod (DevOpsBase's own defaults were `RheemDevOps-MDP-NONPROD` / `RheemDevOps-MDP-PROD`, which won't exist in your org).

**Where to get it:**
- Ask the DevOps team which pool(s) are provisioned for Databricks CI/CD jobs, or
- Check yourself: ADO project → **Project Settings → Agent Pools**.

**How to verify:** If the pool name is wrong or you lack access, the stage will fail immediately with "no agent pool found" or hang waiting for an agent that never picks up the job.

---

## 3. Variable groups (per environment)

**Where:** `azure-pipelines-databricks-bundles.yml:53-55`
```yaml
# variableGroupDev: <DEV_VARIABLE_GROUP>
# variableGroupQa: <QA_VARIABLE_GROUP>
# variableGroupProd: <PROD_VARIABLE_GROUP>
```

**What it needs to become:** Names of ADO **Library → Variable groups**, one per environment. Each group **must define two variables**:

| Variable | Example value | Source |
|---|---|---|
| `DATABRICKS_HOST` | `https://adb-1234567890123456.7.azuredatabricks.net` | Databricks workspace admin (per environment) |
| `BUNDLE_TARGET` | `dev`, `qa`, or `prod` | Must match a target name in `bundles/*/databricks.yml` |

**Where to get it:**
- The **DevOpsBase team** may already have standard variable group names/conventions for other repos on this pattern — ask them first, since reusing existing groups is simpler than creating new ones.
- The **Databricks workspace URL** for each environment comes from whoever administers your Databricks workspaces (platform/data engineering team) — it's the URL you see in the browser when logged into that workspace.
- If groups don't exist yet: ADO project → **Pipelines → Library → + Variable group**, create one per environment, add `DATABRICKS_HOST` (plain text) and `BUNDLE_TARGET` (plain text).

**How to verify:** After deploy, the pipeline log's "Configure Databricks CLI" step runs `databricks auth describe` — a successful, authenticated response confirms `DATABRICKS_HOST` (and the token from the service connection) are correct.

---

## 4. Service connections (per environment)

**Where:** `azure-pipelines-databricks-bundles.yml:56-58`
```yaml
# azureServiceConnectionDev: <DEV_SERVICE_CONNECTION>
# azureServiceConnectionQa: <QA_SERVICE_CONNECTION>
# azureServiceConnectionProd: <PROD_SERVICE_CONNECTION>
```

**What it needs to become:** Names of ADO **Service connections** (Azure Resource Manager type), each backed by a **service principal (SPN)** that has permission to obtain an Azure AD token for the target Databricks workspace (resource ID `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d`) — one SPN per environment, ideally scoped so the Dev SPN cannot touch the Prod workspace.

**Where to get it:**
- Ask the **DevOps team** whether environment-scoped SPNs/service connections already exist for Databricks (likely yes, if other repos already use this DevOpsBase pattern).
- If new ones are needed, that requires an **Azure AD / Entra ID admin** to create the SPN and grant it access on the Databricks workspace (via Databricks account console or workspace admin, "Add service principal"), then a **project admin** to register it in ADO: **Project Settings → Service connections → New service connection → Azure Resource Manager**.

**How to verify:** The "Get Databricks token" step (`AzureCLI@2` task in the DevOpsBase deploy template) will fail with an auth error if the SPN lacks permission — check that step's log first if a deploy fails early.

---

## 5. Prod environment name + approvals

**Where:** `azure-pipelines-databricks-bundles.yml:59`
```yaml
# prodEnvironment: PROD
```

**What it needs to become:** The name of an ADO **Environment** (Pipelines → Environments) with **approval checks** configured — this is the actual approval gate described in the adoption plan's section 4 (1 approver on Prod).

**Where to get it:**
- Ask the DevOps team if a shared `PROD` environment convention already exists, or if this repo should have its own.
- To create/configure it yourself: ADO project → **Pipelines → Environments → New environment** (or reuse existing) → open it → **⋮ (Approvals and checks) → Approvals** → add the approver(s) — typically the tech lead or release owner per the adoption plan.

**Who decides the approver:** This is a people/process decision, not a technical lookup — confirm with your engineering lead who should be the Prod approver(s).

**How to verify:** Trigger a run with `deployProd: true`; the Prod stage should pause in "Waiting for approval" state and notify the configured approver(s) before deploying.

---

## 6. Real bundle paths

**Where:** `azure-pipelines-databricks-bundles.yml:46`
```yaml
bundlePaths:
  - bundles/sample_data_pipeline # TODO: replace/add real bundle paths
```

**What it needs to become:** One entry per real Databricks Asset Bundle folder in this repo, each containing its own `databricks.yml`.

**Where to get it:** This one's on you/your team — it's determined by which actual data pipelines, ETL jobs, or Data APIs you're migrating into this repo, not by the DevOps team. Use [`bundles/sample_data_pipeline/`](bundles/sample_data_pipeline/) as the folder-structure template (`databricks.yml` + `resources/*.yml` + `src/`), then delete the sample once real bundles are in place.

**How to verify:** `databricks bundle validate -t dev` (run locally with the Databricks CLI, pointed at a dev workspace) should succeed for each bundle path before it's added to the pipeline.

---

## Suggested order of operations

1. Get the **DevOpsBase repo path** (#1) and confirm this pipeline has permission to reference it — nothing else works without this.
2. Confirm **agent pools** (#2) and **service connections** (#4) with the DevOps team — these are usually already standardized org-wide.
3. Confirm or create **variable groups** (#3), which requires the Databricks workspace URLs from whoever admins those workspaces.
4. Set up the **Prod environment + approver** (#5) with your engineering lead.
5. Replace the **sample bundle** with real bundle folder(s) (#6) as pipelines are ready to migrate.
6. Uncomment the override block in `azure-pipelines-databricks-bundles.yml`, fill in the confirmed values, remove the `TODO` comments, and register the pipeline in Azure DevOps.
