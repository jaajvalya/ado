# Deploying This Repo in Azure DevOps — Step by Step

This walks through taking everything already scaffolded in this repo — [`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml), [`azure-pipelines-ci-secret-scan.yml`](azure-pipelines-ci-secret-scan.yml), the sample bundle, branch policies, approvals — and actually standing it up in an Azure DevOps (ADO) project.

> **Heads up:** this repo's current `origin` remote is GitHub (`jaajvalya/ado`), but every other doc in this repo ([`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md), branch policies, PR approvals) is written in Azure Repos terms. Step 1 below covers moving/pushing this code into an Azure Repos project. If you actually intend to keep hosting on GitHub and only use Azure **Pipelines** against it, most steps still apply but branch policy/PR steps would instead be GitHub branch protection — flag that if it's the real intent, since this guide assumes Azure Repos throughout.

Do these roughly in order — later steps depend on earlier ones existing.

---

## 0. Prerequisites

- An Azure DevOps **organization** and a **project** to hold this repo (ask the DevOps team if one already exists for this initiative, per [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md))
- You (or whoever runs this setup) needs **Project Administrator** (or equivalent) permissions to create pipelines, service connections, environments, and branch policies
- Azure CLI or the `az devops` extension installed locally is optional but convenient: `az extension add --name azure-devops`

---

## 1. Get the code into Azure Repos

If the ADO project doesn't have this repo yet:

1. ADO → your project → **Repos** → if empty, it offers **Import a repository**
2. Choose **Import**, source URL = `https://github.com/jaajvalya/ado.git`, or push directly:

```bash
git remote add ado https://dev.azure.com/<org>/<project>/_git/<repo>
git push ado main
```

3. Decide whether `origin` stays GitHub (mirror) or is repointed to ADO as the source of truth. For the rest of this guide, ADO Repos is the one branch policies and PRs apply to.

---

## 2. Confirm access to the DevOpsBase repo

[`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml) references a shared `DevOpsBase` repo via `extends` (see [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #1).

1. Ask the DevOps team for the exact `<Project>/DevOpsBase` path
2. Confirm this project/pipeline has permission to reference it (ADO → the DevOpsBase project → **Project Settings → Repositories → DevOpsBase → Security**, or ask the DevOps team to grant it)
3. Edit line 36 of `azure-pipelines-databricks-bundles.yml` with the real path (commit this change — see step 8)

---

## 3. Confirm or create agent pools

Needed by both pipelines (`nonProdPool`/`prodPool` in the bundles pipeline, `pool.name` in the secret-scan pipeline).

1. ADO → **Project Settings → Agent Pools** — check what already exists
2. If nothing suitable exists, ask the DevOps team to provision one (self-hosted agent pools are usually centrally managed)
3. Note the exact pool names for step 8

---

## 4. Set up service connections (SPNs) per environment

Needed for the pipeline to obtain a Databricks token per environment (see [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #4).

1. Confirm with the DevOps team / Azure AD admin whether Dev/QA/Prod service principals already exist for Databricks access
2. If not, have an Entra ID admin create one SPN per environment and grant it access on the corresponding Databricks workspace (Databricks account console → workspace → **Add service principal**)
3. Register each as an ADO service connection: **Project Settings → Service connections → New service connection → Azure Resource Manager** → link the SPN → name it clearly (e.g. `DBX-Dev-SP`, `DBX-QA-SP`, `DBX-Prod-SP`)
4. Note the three connection names for step 8

---

## 5. Create variable groups per environment

Each stage needs `DATABRICKS_HOST` and `BUNDLE_TARGET` (see [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #3).

1. Get each environment's Databricks workspace URL from whoever admins those workspaces
2. ADO → **Pipelines → Library → + Variable group**
3. Create three groups (e.g. `DEVQBX`, `QADBX`, `PRODDBX` or your own naming), each with:
   - `DATABRICKS_HOST` = the workspace URL for that environment
   - `BUNDLE_TARGET` = `dev`, `qa`, or `prod` respectively (must match the target names in [`bundles/sample_data_pipeline/databricks.yml`](bundles/sample_data_pipeline/databricks.yml))
4. If secrets need to come from Key Vault rather than being typed directly into the variable group, use **Link secrets from an Azure key vault** on the variable group instead
5. Note the three group names for step 8

---

## 6. Create the Prod environment with approval gate

1. ADO → **Pipelines → Environments → New environment** (name it e.g. `PROD`, matching what you'll set as `prodEnvironment`)
2. Open it → **⋮ → Approvals and checks → Approvals**
3. Add the approver(s) — confirm with your engineering lead who this should be (see [`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md) Approver section)
4. Note the environment name for step 8

Dev and QA stages run as regular jobs in the DevOpsBase template (not `deployment` jobs), so they don't need their own ADO Environment object — only Prod does.

---

## 7. Register the secret-scan pipeline first

Do this one before the bundles pipeline so it can be wired into branch policy in step 9.

1. Fill in the pool placeholder in [`azure-pipelines-ci-secret-scan.yml`](azure-pipelines-ci-secret-scan.yml) (`<NONPROD_AGENT_POOL>`) using the pool from step 3
2. Commit and push that change
3. ADO → **Pipelines → New pipeline** → select this repo → **Existing Azure Pipelines YAML file** → pick `/azure-pipelines-ci-secret-scan.yml`
4. Save (don't run yet — it triggers on PRs, not manually, though you can run it once to confirm it works)
5. Run it once manually to confirm gitleaks installs and scans cleanly against the current repo content

---

## 8. Fill in and register the bundles pipeline

1. Edit [`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml):
   - Line 36: real `DevOpsBase` path (step 2)
   - Uncomment and fill the override block (lines 51–59) with the pool, variable group, service connection, and environment names/paths from steps 3–6
   - Line 46: replace `bundles/sample_data_pipeline` with real bundle path(s) once you have them (the sample can stay temporarily if you're just validating plumbing)
2. Commit and push
3. ADO → **Pipelines → New pipeline** → select this repo → **Existing Azure Pipelines YAML file** → pick `/azure-pipelines-databricks-bundles.yml`
4. Save. Run it once manually with `deployDev: true`, `deployQa: false`, `deployProd: false` to confirm the Dev stage deploys cleanly before enabling QA/Prod

---

## 9. Configure branch policies on `main`

This is what actually enforces review and the secret scan from [`SECRETS-POLICY.md`](SECRETS-POLICY.md) and the review flow from [`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md).

1. ADO → **Project Settings → Repositories → `main` → Policies**
2. **Require a minimum number of reviewers**: turn on, set count (typically 1–2), and turn **off** "Allow requestors to approve their own changes"
3. **Build Validation → +**: select the secret-scan pipeline (step 7) → check **Automatically queue on source update** → set **Required**
4. Optionally add a second Build Validation for the bundles pipeline (or a `databricks bundle validate`-only variant) if you want PR-time validation of bundle correctness, not just deploy-time
5. Save

---

## 10. Lock down who can bypass policy

1. ADO → **Project Settings → Repositories → `main` → Security**
2. Find the **"Bypass policies when completing pull requests"** permission
3. Ensure it's only **Allow** for the Team Lead / repo admin group, and explicitly **Deny** (or just not granted) for the general Developer/Approver group — matches the responsibility split in [`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md)

---

## 11. Verify end-to-end

Run through the full loop once before calling this "live":

1. Create a test branch, make a trivial change, push, open a PR into `main` ([`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md) steps 1–6)
2. Confirm the secret-scan build validation runs automatically and shows as required
3. Get it approved, merge with **squash and merge**, delete the branch (steps 7–9)
4. Manually trigger `azure-pipelines-databricks-bundles.yml` with all three stages enabled
5. Confirm Dev and QA deploy, then Prod pauses on **"Waiting for approval"**
6. Have the configured approver approve it and confirm Prod deploys
7. Intentionally test a bypass (on a throwaway PR) to confirm only the intended group can do it, then revert/clean up that test PR

---

## 12. Roll out to the team

Once verified, share with the team:

- [`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md) — day-to-day workflow, by role
- [`SECRETS-POLICY.md`](SECRETS-POLICY.md) — including the one-time local `pre-commit install` step every developer needs to run
- [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) — for reference if new bundles/environments get added later
- [`ADO-CICD-Adoption-Plan.md`](ADO-CICD-Adoption-Plan.md) — the overall model this setup implements
