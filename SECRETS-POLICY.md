# Secrets, Keys & Credentials Policy

## Rule

No secrets, API keys, tokens, passwords, connection strings, or credential files may ever be committed to this repository, hardcoded in pipeline YAML, or hardcoded in bundle/job/notebook code. Secrets flow **only** through Azure Key Vault-backed ADO variable groups and service-connection-issued tokens, resolved at pipeline runtime — never checked into source.

This applies equally to real values and to files that merely *look* like credential files (e.g., a `.env` with placeholder-but-real-shaped values).

## What counts as a secret here

- Databricks personal access tokens (PATs) or OAuth tokens
- Service principal client secrets / certificates
- Storage account keys, SAS tokens, connection strings
- Database usernames/passwords or JDBC connection strings with credentials embedded
- API keys for any third-party service
- `.pem` / `.key` / `.pfx` / `.p12` / `.crt` certificate or private key files
- `.env` files containing real values (an `.env.example` with placeholder values is fine)
- Any `DATABRICKS_TOKEN`, `DATABRICKS_HOST` value hardcoded in `databricks.yml` instead of coming from the pipeline's variable group (see [`ADO-CICD-Adoption-Plan.md`](ADO-CICD-Adoption-Plan.md) section 5 and [`bundles/sample_data_pipeline/databricks.yml`](bundles/sample_data_pipeline/databricks.yml), which already keeps these out)

## Enforcement layers

Three independent layers, so a miss at one is caught by the next:

| Layer | File | Runs when | Blocks |
|---|---|---|---|
| 1. Ignore known secret file patterns | [`.gitignore`](.gitignore) | Always (local) | Common credential file types from ever being staged |
| 2. Pre-commit secret scan | [`.pre-commit-config.yaml`](.pre-commit-config.yaml) (gitleaks) | Every local `git commit` | Committing a detected secret, before it ever reaches git history |
| 3. CI secret scan (required PR check) | [`azure-pipelines-ci-secret-scan.yml`](azure-pipelines-ci-secret-scan.yml) | Every PR into `main` | Merging, even if layer 1/2 were bypassed or skipped |

Layer 3 is the one that actually *enforces* the policy for the team — layers 1–2 are convenience/early-warning for individual developers, but nothing stops someone from deleting their local hook. The PR-time gitleaks scan wired in as a **required Build Validation policy** is what makes this non-optional.

Both scan pipelines (layer 2 and 3) use the same rules via [`.gitleaks.toml`](.gitleaks.toml), which extends gitleaks' default rule set (PATs, cloud provider keys, private keys, generic high-entropy secrets, etc.) plus an allowlist for this repo's own non-secret placeholder tokens (e.g. `<AZURE_DEVOPS_PROJECT>`).

## One-time setup

### Every developer (local)

```bash
pip install pre-commit
pre-commit install
```

After this, `git commit` runs gitleaks automatically and blocks the commit if it detects a secret.

### Repo/project admin (Azure DevOps)

1. Register [`azure-pipelines-ci-secret-scan.yml`](azure-pipelines-ci-secret-scan.yml) as a pipeline (after filling in the agent pool placeholder — see [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #2).
2. **Project Settings → Repositories → `main` → Policies → Build Validation → +** → select the secret-scan pipeline → check **Automatically queue on source update** → set **Required**.
3. Optional, if licensed for it: also enable Azure DevOps' built-in **Credential Scanner** extension as an additional layer.

Until step 2 is done, the scan pipeline exists but does not actually block anything — a PR can still merge without it running. Confirm the policy shows as "Required" before treating this as enforced.

## If gitleaks flags something

- **Real secret:** treat it as compromised the moment it's committed, even locally — rotate/revoke it immediately, then remove it from git history (`git filter-repo` or BFG) before the branch is safe to push or merge. Do not just delete the line in a new commit; the old value stays in history.
- **False positive** (e.g., an example UUID, a placeholder like `<DEV_SERVICE_CONNECTION>`, a test fixture): add a scoped rule to [`.gitleaks.toml`](.gitleaks.toml)'s `[allowlist]` and note why in a comment. Don't reach for `git commit --no-verify` or `--exit-code 0` to route around it — that silently disables the check for everyone reusing the same pattern later.

## Where real secrets live instead

- **Azure Key Vault**, referenced via ADO variable groups, for `DATABRICKS_HOST` / tokens — see [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #3
- **ADO service connections** (Azure AD service principals) for pipeline authentication — no static PATs stored anywhere — see [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #4
- **Databricks secret scopes** for anything a notebook or job needs to read at runtime (`dbutils.secrets.get(...)`) — never hardcoded in `src/*.py` or `resources/*.yml`
