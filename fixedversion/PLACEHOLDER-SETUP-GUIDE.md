# Placeholder Setup Guide

> Fixed copy — Key Vault vs plain vars, PR CI registration, no fragile line numbers.
> Original: `../PLACEHOLDER-SETUP-GUIDE.md`

Work top to bottom. Later items depend on earlier ones.

---

## Quick reference

| # | Placeholder | Where | Get it from |
|---|---|---|---|
| 1 | DevOpsBase repo path | `azure-pipelines-databricks-bundles.yml` → `resources.repositories` | DevOps team |
| 2 | Agent pools (non-prod / prod), Linux-capable | CD + PR CI + secret-scan `pool` / parameters | DevOps / ADO Agent Pools |
| 3 | Variable groups (dev/qa/prod) | CD pipeline parameters | DevOps + Databricks admin |
| 4 | Key Vault link (secrets only) | ADO Library → each variable group | DevOps + Azure subscription admin |
| 5 | Service connections (dev/qa/prod) | CD pipeline parameters | DevOps / Entra ID admin |
| 6 | Prod environment + approvers | CD `prodEnvironment` + ADO Environments UI | DevOps + engineering lead |
| 7 | Real bundle paths | CD `bundlePaths` | Your team |
| 8 | Register pipelines + branch policies | ADO Pipelines + Repo Policies | Repo admin |

Org-specific string values still must be filled before first real run — this fixed version makes them **required and explicit** so the pipeline does not silently fall back to another org’s defaults.

---

## 1. DevOpsBase repository path

**Where:** `azure-pipelines-databricks-bundles.yml` → `resources.repositories[].name`

```yaml
name: "<AZURE_DEVOPS_PROJECT>/DevOpsBase"
```

Replace with `"<Your ADO Project>/DevOpsBase"`.

**Verify:** Pipeline save/queue fails at parse time if the repo path or permissions are wrong.

**Also:** Authorize this pipeline to use the DevOpsBase repository resource.

---

## 2. Agent pools

**Where:**
- CD parameters: `nonProdPool`, `prodPool`
- PR CI / secret-scan: `pool.name`

Use pools that can run **Linux** scripts (gitleaks linux_x64 tarball and bash `set -e` in secret scan / PR CI). If only Windows pools exist, change the install steps before go-live.

**Verify:** Wrong name → “no agent pool found” or queue never picked up.

---

## 3. Variable groups (per environment)

**Where:** CD parameters `variableGroupDev` / `variableGroupQa` / `variableGroupProd`

Each group **must** define these **plain-text** (non-secret) variables:

| Variable | Example | Notes |
|---|---|---|
| `DATABRICKS_HOST` | `https://adb-….azuredatabricks.net` | Workspace URL — **not** a secret |
| `BUNDLE_TARGET` | `dev` / `qa` / `prod` | Must match a target in `bundles/*/databricks.yml` |

**Verify:** Deploy log “Configure Databricks CLI” / `databricks auth describe` succeeds when host + service connection are correct.

---

## 4. Key Vault link (secrets only)

**When needed:** Any secret that must appear as an ADO variable (storage keys, API keys, etc.). Databricks **auth for the pipeline** should use the **service connection**, not a PAT in the variable group.

**How:**
1. ADO → **Pipelines → Library →** open the variable group  
2. **Link secrets from an Azure key vault** → pick the service connection + vault  
3. Add only secret names that jobs/pipelines need  
4. Mark them secret; never commit values

Do **not** move `DATABRICKS_HOST` or `BUNDLE_TARGET` into Key Vault unless your org mandates it.

Notebook/job runtime secrets belong in **Databricks secret scopes**, not in git.

---

## 5. Service connections (per environment)

**Where:** CD parameters `azureServiceConnectionDev` / `Qa` / `Prod`

ARM service connections backed by SPNs that can obtain an AAD token for Databricks (`2ff814a6-3304-4ab8-85cb-cd0e6f879c1d`). One SPN per env; Dev SPN must not access Prod.

**Verify:** DevOpsBase “Get Databricks token” / `AzureCLI@2` step fails early if the SPN lacks rights.

---

## 6. Prod environment name + approvals

**Where:** CD parameter `prodEnvironment` (e.g. `PROD`)

ADO → **Pipelines → Environments** → Approvals and checks → add approver(s) (tech lead / release owner).

**Verify:** Run with Prod enabled; stage waits for approval before deploy.

---

## 7. Real bundle paths

**Where:** CD parameter `bundlePaths`

Each path must contain a `databricks.yml`. Use `bundles/sample_data_pipeline` only as a template — **remove it before first production deploy** and point at real bundles.

**Verify (local):** `databricks bundle validate -t dev` for each path.

---

## 8. Register pipelines + branch policies (required)

1. Register [`azure-pipelines-ci-pr.yml`](azure-pipelines-ci-pr.yml) — PR build validation (lint, unit, bundle validate, secret scan).
2. Optionally register [`azure-pipelines-ci-secret-scan.yml`](azure-pipelines-ci-secret-scan.yml) as an extra Required check.
3. Register [`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml) — CD on `main` only.
4. Branch policies on `main`:
   - Minimum number of reviewers; **no** requester approve
   - Build Validation: PR CI (and secret scan if separate) → **Required**
   - Prefer squash merge as policy/default
5. Confirm CD has **no** PR trigger (fixed YAML already omits `pr:`).

Until step 4 marks checks **Required**, secret scan / PR CI do not enforce the policy.

---

## Suggested order of operations

1. DevOpsBase path + repo permission (#1)
2. Agent pools (#2) and service connections (#5)
3. Variable groups plain vars (#3); Key Vault link only for secrets (#4)
4. Prod Environment + approvers (#6)
5. Register pipelines + Required branch policies (#8)
6. Replace sample bundle with real paths (#7); delete sample before prod
7. Confirm with DevOps that DevOpsBase honors **sequential** DEV→QA→PROD (`docs/DEVOPSBASE-CONTRACT.md`)
