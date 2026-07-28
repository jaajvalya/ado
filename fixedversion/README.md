# Fixed version (do not overwrite originals)

Corrected copies of the plan, guides, policies, pipelines, and sample bundle that address the **highlighted gaps** from `VALIDATION-ISSUES-AND-GAPS.txt`.

Original files at the repo root are unchanged. To adopt these fixes, copy or merge from this folder intentionally.

## What was fixed here

| Highlighted gap | Fix in this folder |
|---|---|
| Plan vs reality (lint / unit / validate / regression missing) | `azure-pipelines-ci-pr.yml`, `pyproject.toml`, `tests/`, `regression/`, enriched pre-commit |
| Sequential vs parallel contradiction | Plan §5 aligned to Dev → QA → Prod; CD docs + DevOpsBase contract |
| Key Vault vs plain-text variable groups | `PLACEHOLDER-SETUP-GUIDE.md` + `SECRETS-POLICY.md` clarify HOST (plain) vs secrets (Key Vault) |
| Pipelines not runnable / wrong defaults | CD parameters required & explicit; no silent foreign-org defaults |
| PR may trigger full CD | CD has **no** `pr:` trigger; PR uses validate-only `azure-pipelines-ci-pr.yml` |
| Sample bundle not env-ready | Per-env catalogs, cluster policy id, variables in `bundles/sample_data_pipeline/` |

## Suggested adoption order

1. Review docs in this folder against your org names.
2. Fill placeholders listed in `PLACEHOLDER-SETUP-GUIDE.md`.
3. Copy pipelines + bundle + test tooling into the repo root when ready.
4. Register pipelines and branch policies as described in the setup guide.
