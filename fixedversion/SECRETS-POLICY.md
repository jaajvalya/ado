# Secrets, Keys & Credentials Policy

> Fixed copy — clarifies what is a secret vs plain config; Key Vault usage.
> Original: `../SECRETS-POLICY.md`

## Rule

No secrets, API keys, tokens, passwords, connection strings, or credential files may ever be committed to this repository, hardcoded in pipeline YAML, or hardcoded in bundle/job/notebook code.

Secrets flow **only** through:
1. **ADO service connections** (preferred for Databricks auth — SPN token at pipeline runtime), and/or
2. **Azure Key Vault-backed** secret variables in ADO variable groups

Never check secrets into source.

This applies to real values and to files that merely *look* like credential files (e.g. a `.env` with real-shaped values).

## What is a secret vs plain config

| Item | Secret? | Where it lives |
|---|---|---|
| Databricks PAT / OAuth refresh material | Yes | Prefer service connection only; never git; never plain Library vars |
| Service principal client secret / cert | Yes | Service connection / Key Vault only |
| Storage keys, SAS, DB passwords, API keys | Yes | Key Vault → variable group secret, or Databricks secret scope |
| `.pem` / `.key` / `.pfx` / `.p12` / private keys | Yes | Never in git |
| `.env` with real values | Yes | Never in git (`.env.example` with placeholders is OK) |
| `DATABRICKS_HOST` (workspace URL) | **No** | ADO variable group **plain text** |
| `BUNDLE_TARGET` (`dev` / `qa` / `prod`) | **No** | ADO variable group **plain text** |
| Catalog / schema names | **No** | Bundle target variables in `databricks.yml` (non-secret) |

Do **not** put `DATABRICKS_HOST` in Key Vault unless your org standard requires it; it is not a credential. Do **not** hardcode host or tokens in `databricks.yml`.

## Enforcement layers

| Layer | File | Runs when | Blocks |
|---|---|---|---|
| 1. Ignore credential file patterns | [`.gitignore`](.gitignore) | Always (local) | Common secret files from staging |
| 2. Pre-commit secret scan | [`.pre-commit-config.yaml`](.pre-commit-config.yaml) (gitleaks) | Every local `git commit` | Commit of detected secrets |
| 3. PR CI secret scan | [`azure-pipelines-ci-pr.yml`](azure-pipelines-ci-pr.yml) and/or [`azure-pipelines-ci-secret-scan.yml`](azure-pipelines-ci-secret-scan.yml) | Every PR into `main` | Merge when Build Validation is **Required** |

Layer 3 is the team enforcement layer. Until Build Validation is Required in ADO, the pipeline can exist without blocking merges — confirm policy shows **Required**.

Both local and CI scans use [`.gitleaks.toml`](.gitleaks.toml) (default rules + an **explicit** allowlist of known placeholders only).

## One-time setup

### Every developer (local)

```bash
pip install pre-commit
pre-commit install
```

### Repo/project admin (Azure DevOps)

1. Fill agent pool placeholders (Linux-capable pool for gitleaks/CLI steps) — [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md).
2. Register [`azure-pipelines-ci-pr.yml`](azure-pipelines-ci-pr.yml) (and optionally the dedicated secret-scan pipeline).
3. **Project Settings → Repositories → `main` → Policies → Build Validation → +** → select the PR CI (and/or secret-scan) pipeline → **Automatically trigger** → **Required**.
4. Optional: enable Azure DevOps **Credential Scanner** if licensed.

## If gitleaks flags something

- **Real secret:** rotate/revoke immediately; purge from git history (`git filter-repo` / BFG) before merge. Deleting in a new commit is not enough.
- **False positive:** add a **specific** allowlist entry in [`.gitleaks.toml`](.gitleaks.toml) with a comment explaining why. Do not use `--no-verify` or weaken CI exit codes.

## Where real secrets live instead

- **Service connections** — Databricks auth for pipelines ([`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) service connections section)
- **Azure Key Vault** linked to variable groups — only for values that are actually secret
- **Databricks secret scopes** — runtime secrets for notebooks/jobs (`dbutils.secrets.get(...)`)
