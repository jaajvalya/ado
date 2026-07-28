# Azure DevOps CI/CD for Databricks — Adoption Plan

## Expectations
1. Adopt Azure DevOps for Databricks developments (Data Pipelines, Data APIs, ETL)
2. Automate CI/CD
3. Regression Test Automation

## Environments
Databricks Environments:
1. Development (dev)
2. QA (qa)
3. Production (prod)

---

## 1. Development activities to consider

**Source control & repo structure**
- Move all Databricks notebooks/code into Git (Databricks Repos or Git integration) — no more "edit in workspace UI" as source of truth
- Decide repo strategy: monorepo (all pipelines/APIs) vs. multi-repo (per domain/team). Monorepo is easier to govern early on
- Branching strategy: trunk-based (`main` + short-lived feature branches) is the modern default; GitFlow (`develop`/`release`/`main`) if you need longer release cycles

**Packaging & deployment mechanism**
- **Databricks Asset Bundles (DABs)** — the current Databricks-native IaC approach for jobs, workflows, clusters, and permissions as YAML. Use this over ad-hoc REST API scripts or older `dbx` tooling
- Package shared logic as Python wheels/libraries, not copy-pasted notebook cells
- Parameterize per-environment config (catalog names, cluster sizes, secret scopes) via bundle target overrides or ADO variable groups

**Quality gates**
- Unit tests (pytest + Databricks Connect or local Spark session) for transformation logic
- Data quality tests (Great Expectations, dbt tests, or Delta Live Tables expectations) for pipeline output
- Linting/formatting (black, ruff/flake8) as pre-commit hooks and CI step
- Static secret scanning (no hardcoded tokens/keys in notebooks)

**Environment & security**
- Service principals per environment (dev/qa/prod), not personal Databricks tokens, for pipeline auth
- Secrets in Azure Key Vault, referenced via ADO variable groups linked to Key Vault — never in YAML
- Unity Catalog: separate catalogs (or catalog-per-env) for data isolation between dev/qa/prod
- Cluster policies to control cost (job clusters over all-purpose clusters for scheduled pipelines)

**Regression testing**
- A dedicated regression suite (data contract checks, row-count/schema diffs, key business-rule assertions) that runs post-deploy in QA before promotion — this is Expectation #3 and needs its own pipeline stage, not just unit tests

---

## 2. Workflow / process flow

```
Feature branch → PR → main
        │
        ▼
   CI (on PR):  lint → unit tests → bundle validate → build artifact
        │  (required check before merge)
        ▼
   Merge to main
        │
        ▼
   CD → Deploy to DEV (automatic)
        │
        ▼
   Run integration/smoke tests in DEV (automatic)
        │
        ▼
   Promote to QA (automatic trigger, gated approval optional)
        │
        ▼
   Run REGRESSION SUITE in QA (automatic)
        │
        ▼
   Approval gate (QA lead / tech lead sign-off)
        │
        ▼
   Promote to PROD (manual trigger or scheduled release window)
        │
        ▼
   Approval gate (release owner / change record)
        │
        ▼
   Deploy to PROD → post-deploy smoke test → monitor/alert
```

In Azure DevOps terms: a multi-stage YAML pipeline with `dev`, `qa`, `prod` **Environments**, each with its own approval checks configured on the Environment (not the pipeline) — this is the standard pattern.

---

## 3. Industry standard approval flow

| Stage | Trigger | Approval | Gate type |
|---|---|---|---|
| PR → main | Developer opens PR | 1–2 required reviewers + passing build validation | Branch policy |
| Dev deploy | Merge to main | None (fully automatic) | — |
| QA deploy | Successful dev + tests | Optional automatic, or 1 approver (QA/tech lead) | Environment approval |
| QA → Prod | Regression suite passes | Required: release manager/product owner (and CAB in regulated orgs) | Environment approval + change ticket |
| Prod deploy | Approval granted | Scheduled release window, documented rollback plan | Environment approval + business hours gate |

Standard ADO mechanisms used: **branch policies** (required reviewers, build validation, comment resolution), **Environment approvals & checks** (manual approvers, business-hours gate, Azure Monitor alert gate, work-item query gate), and **release gates** tied to ITSM/change tickets for prod in larger or regulated orgs.

---

## 4. Practically possible approval and workflow

For most mid-size teams, the full CAB/2-approver-per-prod-deploy model above is overkill and just slows delivery. A pragmatic version:

- **Dev**: fully automatic on merge to `main` — no approval, fast feedback loop
- **QA**: automatic deploy + automatic regression suite; require **1 approver** (whoever owns QA sign-off) only if regression suite passes — don't gate on human review of green tests
- **Prod**: **1 approver** (tech lead or release owner) via ADO Environment approval, not a committee. Add a lightweight change record (a linked work item, not a full ITSM ticket) if audit trail is needed
- Decouple deploy from release using feature flags where possible, so prod deploys can happen more often (even daily) without waiting for a "release event" — reduces pressure on the approval step
- Rollback plan = redeploy the previous pipeline artifact/bundle version, not a manual undo — this only works if the CD is idempotent and artifact-versioned, so build that in from day one
- Start with approval **only on prod**; add a QA gate later if regression failures start slipping through

---

---

## 5. Concrete implementation — DevOpsBase shared template

The DevOps team already maintains a reusable Dev → QA → Prod pipeline for Databricks Asset Bundles in a `DevOpsBase` repo (`databricks-asset-bundle-cicd-base.yaml` + `templates/databricks-asset-bundle-deploy-template.yaml`). Consumer repos don't copy deploy logic — they `extends` the base template and pass their bundle paths. This repo now follows that pattern:

```
ado/
├── azure-pipelines-databricks-bundles.yml   # consumer pipeline, extends DevOpsBase
└── bundles/
    └── sample_data_pipeline/                # placeholder — rename/replace with real pipelines
        ├── databricks.yml                   # bundle def: dev/qa/prod targets
        ├── resources/
        │   └── sample_job.yml               # job/cluster/schedule definition
        └── src/
            └── sample_notebook.py           # pipeline code
```

**How it maps to sections 2–4 above:**
- Dev and QA stages run in parallel (no ordering dependency between them)
- Prod always `dependsOn` QA succeeding — matches the "1 approver on Prod, gated by passing regression/QA" model from section 4
- Prod uses an ADO **Environment** (`prodEnvironment`) with manual approval checks configured on it — this is where the approval gate lives, not in the YAML itself
- `BUNDLE_TARGET` and `DATABRICKS_HOST` come from per-environment ADO **variable groups**, keeping secrets and host config out of source

**Placeholders still needed from the client/DevOps team** (marked as `TODO` / `<PLACEHOLDER>` in `azure-pipelines-databricks-bundles.yml`):
- Real ADO project/repo path for the `DevOpsBase` repository resource (`"<AZURE_DEVOPS_PROJECT>/DevOpsBase"`)
- Agent pool names (non-prod / prod)
- Variable group names per environment, each must define `DATABRICKS_HOST` and `BUNDLE_TARGET`
- Service connection names per environment (SPNs with Databricks token permissions)
- Prod ADO Environment name, with approvals configured on it
- Real bundle folder(s) under `bundles/` in place of the `sample_data_pipeline` placeholder

Once those are confirmed, uncomment and fill the override block in `azure-pipelines-databricks-bundles.yml` and register the file as an Azure DevOps pipeline.
