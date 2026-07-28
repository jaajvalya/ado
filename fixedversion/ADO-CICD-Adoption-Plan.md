# Azure DevOps CI/CD for Databricks — Adoption Plan

> Fixed copy — aligns process, DevOpsBase usage, and repo artifacts.
> Original: `../ADO-CICD-Adoption-Plan.md`

## Expectations
1. Adopt Azure DevOps for Databricks developments (Data Pipelines, Data APIs, ETL)
2. Automate CI/CD
3. Regression Test Automation

## Environments
Databricks Environments:
1. Development (dev)
2. QA (qa)
3. Production (prod)

**Repo strategy (decided for this project):** monorepo with one or more bundles under `bundles/<pipeline_name>/`.

---

## 1. Development activities to consider

**Source control & repo structure**
- Move all Databricks notebooks/code into Git — no more "edit in workspace UI" as source of truth
- Monorepo: all pipelines/APIs under `bundles/`
- Branching strategy: trunk-based (`main` + short-lived `feature/*`, `bugfix/*`, `hotfix/*`)

**Packaging & deployment mechanism**
- **Databricks Asset Bundles (DABs)** for jobs, workflows, clusters, and permissions as YAML
- Package shared logic as Python wheels/libraries under each bundle's `artifacts/` (or a shared `libs/` path) — not copy-pasted notebook cells
- Parameterize per-environment config (catalog names, cluster sizes, secret scopes, cluster policies) via bundle target overrides; host/auth via ADO variable groups + service connections

**Quality gates (implemented in this fixed version)**
- Unit tests: `pytest` under `tests/` (local Spark or Databricks Connect)
- Lint/format: `ruff` (+ format) via pre-commit and PR CI
- Bundle validate: `databricks bundle validate` on every PR (no deploy)
- Secret scanning: gitleaks locally + required PR build validation
- Regression suite: `regression/` runs post-deploy in QA before Prod promotion
- Smoke tests: lightweight post-deploy checks in DEV and PROD (see `regression/smoke/`)

**Environment & security**
- Service principals per environment (dev/qa/prod) via ADO service connections — not personal Databricks tokens
- **Non-secret** config (`DATABRICKS_HOST`, `BUNDLE_TARGET`) in ADO variable groups as plain text
- **Secrets** (if any must live in Library) only via Azure Key Vault-linked variable group secrets — never in YAML or notebooks
- Unity Catalog: separate catalogs per env (`<prefix>_dev`, `<prefix>_qa`, `<prefix>_prod`) via bundle target variables
- Cluster policies per env for cost control (job clusters; `policy_id` on clusters)

**Regression testing**
- Dedicated suite in `regression/` (schema/row-count/contract checks) executed in the **QA** stage after deploy and **before** Prod approval — Expectation #3

---

## 2. Workflow / process flow (authoritative)

```
Feature branch → PR → main
        │
        ▼
   CI (on PR only — no deploy):
        secret scan → lint → unit tests → bundle validate
        │  (required build validation before merge)
        ▼
   Merge to main
        │
        ▼
   CD (main only) → Deploy to DEV
        │
        ▼
   Smoke tests in DEV
        │
        ▼
   Deploy to QA  (depends on successful DEV + smoke)
        │
        ▼
   REGRESSION SUITE in QA
        │
        ▼
   Approval gate on Prod ADO Environment (tech lead / release owner)
        │
        ▼
   Deploy to PROD → post-deploy smoke → monitor/alert
```

**Ordering rule:** stages are **sequential**: DEV → QA → PROD. QA must not start until DEV deploy + smoke succeed. PROD must not start until QA deploy + regression succeed and the Environment approval is granted.

In Azure DevOps: multi-stage YAML with `dev`, `qa`, `prod` **Environments**. Approvals live on the Prod Environment (not hardcoded approver lists in YAML).

---

## 3. Industry standard approval flow

| Stage | Trigger | Approval | Gate type |
|---|---|---|---|
| PR → main | Developer opens PR | 1–2 required reviewers + passing PR CI | Branch policy |
| Dev deploy | Merge to main | None (automatic) | — |
| QA deploy | Successful DEV + smoke | None (automatic) | Stage `dependsOn` |
| QA → Prod | Regression suite passes | Required: release owner / tech lead | Environment approval |
| Prod deploy | Approval granted | Business hours / change record as needed | Environment checks |

---

## 4. Practically possible approval and workflow

- **Dev**: automatic on merge to `main`
- **QA**: automatic after DEV; regression must pass; no human gate on green tests
- **Prod**: **1 approver** via ADO Environment approval; link a work item for audit if required
- Prefer feature flags to decouple deploy from release when the product supports it (optional; pattern left to each pipeline team)
- **Rollback** = redeploy the previous known-good bundle/artifact version — see `docs/ROLLBACK.md`
- **Hotfix**: `hotfix/*` → PR (same CI) → merge → full CD path (DEV→QA→PROD). Do not skip QA regression except under documented bypass with Manager sign-off — see `GIT-WORKFLOW-GUIDE.md`

---

## 5. Concrete implementation — DevOpsBase + local CI

```
fixedversion/   (or repo root after adoption)
├── azure-pipelines-ci-pr.yml              # PR only: lint, unit, bundle validate (+ secret scan)
├── azure-pipelines-ci-secret-scan.yml     # Optional dedicated secret-scan pipeline for branch policy
├── azure-pipelines-databricks-bundles.yml # CD only on main: DEV → QA → PROD via DevOpsBase
├── bundles/sample_data_pipeline/          # env-parameterized sample; replace with real bundles
├── tests/                                 # unit tests
├── regression/                            # QA regression + smoke helpers
└── docs/DEVOPSBASE-CONTRACT.md            # required behavior from the shared template
```

**How it maps to sections 2–4:**
- **PR builds never deploy.** CD pipeline has no `pr:` trigger. Validation on PRs is `azure-pipelines-ci-pr.yml`.
- **CD is sequential:** DEV then QA then PROD (`dependsOn`). If the shared DevOpsBase template currently runs Dev∥QA, this org must use a sequential mode or equivalent stage graph — see `docs/DEVOPSBASE-CONTRACT.md`. Do not document parallel Dev/QA as the process.
- Prod uses ADO Environment (`prodEnvironment`) with manual approval checks.
- `BUNDLE_TARGET` and `DATABRICKS_HOST` come from per-environment variable groups (plain text). Auth tokens come from service connections at runtime — not from git.

**Placeholders still required from DevOps / platform** (see `PLACEHOLDER-SETUP-GUIDE.md`):
- Real ADO project/repo path for DevOpsBase
- Agent pool names (Linux-capable for secret scan / CLI steps)
- Variable group names + Key Vault link for any secret vars
- Service connection names per environment
- Prod ADO Environment name + approvers
- Real bundle folder(s) replacing `sample_data_pipeline` before production use
