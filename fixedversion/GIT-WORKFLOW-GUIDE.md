# Git & Azure DevOps Workflow Guide

> Fixed copy — PR CI vs CD split, hotfix path, Prod approval.
> Original: `../GIT-WORKFLOW-GUIDE.md`

Step-by-step Git/ADO workflow for this repo.

**Part 1** — operational how-to.
**Part 2** — responsibilities by audience.

Assumes `main` is protected by branch policies (required reviewers + required build validations from `azure-pipelines-ci-pr.yml` and/or `azure-pipelines-ci-secret-scan.yml` per [`SECRETS-POLICY.md`](SECRETS-POLICY.md)) and that PROD deployments use the Environment approval gate in [`ADO-CICD-Adoption-Plan.md`](ADO-CICD-Adoption-Plan.md).

---

## Part 1 — Step by step

### 1. Clone the repo

```bash
git clone https://<org>@dev.azure.com/<org>/<project>/_git/<repo>
cd <repo>
```

Use the clone URL from **ADO → Repos → Clone**.

### 2. Create a branch

Always branch off an up-to-date `main`.

```bash
git checkout main
git pull origin main
git checkout -b feature/<short-description>
# examples: feature/sample-etl-job, bugfix/dev-target-path, hotfix/qa-token-refresh
```

Naming: `feature/…`, `bugfix/…`, `hotfix/…` — short and specific.

### 3. Commit changes

```bash
git add <specific files>
git status
git commit -m "Short, specific summary of the change"
```

With [`.pre-commit-config.yaml`](.pre-commit-config.yaml) installed, commits run gitleaks + ruff. Do not use `--no-verify`.

### 4. Push the branch

```bash
git push -u origin feature/<short-description>
```

### 5. Pull / keep your branch current

```bash
git checkout main
git pull origin main
git checkout feature/<short-description>
git merge main
# resolve conflicts, then:
git push
```

### 6. Create a Pull Request (PR)

- ADO → **Repos → Pull Requests → New Pull Request**
- Source: your branch → Target: `main`
- Title/description: what changed and why; link work item if any; add reviewers

**What runs on PR (validate only — no deploy):**
- [`azure-pipelines-ci-pr.yml`](azure-pipelines-ci-pr.yml) — secret scan, lint, unit tests, `databricks bundle validate`
- Optionally [`azure-pipelines-ci-secret-scan.yml`](azure-pipelines-ci-secret-scan.yml) if registered as a separate required Build Validation

**What does not run on PR:**
- [`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml) — CD only on `main` (no `pr:` trigger)

### 7. Review and Approve

- Read the diff; leave inline comments
- Confirm required pipeline checks are green
- Vote: Approve / Approve with suggestions / Wait for author / Reject
- Self-approval disabled in branch policy

### 8. Merge

Default: **Squash and merge**. Check **Delete source branch after merge**.

### 9. Delete the branch

If not deleted at complete time:

```bash
git push origin --delete feature/<short-description>
git branch -d feature/<short-description>
```

### 10. Bypass approval (exception — sparingly)

Requires **"Bypass policies when completing pull requests"** (Team Lead / admins only).

- Emergencies only (e.g. active Prod outage)
- Comment on the PR with why, before or immediately after
- Follow up with a retrospective review

### 11. Approving a Production deployment

Separate from PR approval — ADO Environment approval on the Prod stage of the CD pipeline.

- Pipeline pauses at Prod: **Waiting for approval**
- Approve only if QA (including regression) succeeded and the change was properly reviewed
- Reject stops deploy only; `main` is unchanged

### 12. Hotfix path

1. Branch `hotfix/<short-description>` from current `main`
2. Same PR CI as any other change (lint / unit / validate / secret scan)
3. Prefer normal review; bypass only for active outage (step 10) with Manager business sign-off noted on the PR
4. After merge, CD still runs **DEV → smoke → QA → regression → Prod approval → PROD**
5. Do **not** skip QA regression to “save time” unless an explicit incident exception is recorded on the pipeline run and the Prod approver acknowledges it

---

## Part 2 — By audience

### Developer

Owns steps **1–6 and 9**. Completes merge (step 8) only if org policy allows author-complete; otherwise Approver/Team Lead completes.

1. Clone, branch, commit, push, open PR
2. Keep branch current with `main`
3. Address review feedback with new commits (no force-push needed for normal review)
4. Never `--no-verify`
5. For hotfixes, follow step 12 — still open a PR

### Team Lead

1. Maintain branch policies on `main` (required reviewers, required PR CI + secret scan, no self-approval)
2. Code review focus on design/correctness
3. Squash merge default
4. Hold bypass permission; document every use
5. Prod Environment approver where appropriate
6. Audit bypasses and policy compliance periodically

### Manager

1. Process oversight; not day-to-day git
2. Business sign-off for high-impact bypass / hotfix exceptions
3. Watch bypass frequency and that secret-scan / PR CI stay Required
4. Escalation for stuck PR disagreements
5. Correct ADO permission levels for new joiners

### Approver

**A. PR Approver**
1. Review correctness, secrets policy, bundle conventions
2. Do not approve around red required checks
3. Never self-approve

**B. Prod Deployment Approver**
1. Distinct from PR approval
2. Verify QA + regression green and PR was not improperly bypassed
3. Reject promptly if something looks wrong

---

## Quick reference

| Action | Who | Where |
|---|---|---|
| Create branch, commit, push | Developer | Local Git |
| Open PR | Developer | ADO Repos |
| PR CI (no deploy) | Automation | `azure-pipelines-ci-pr.yml` |
| Review & Approve | Approver / Team Lead | ADO PR |
| Squash merge | Developer or Approver (per org) | ADO PR |
| CD DEV→QA→PROD | Automation after merge | `azure-pipelines-databricks-bundles.yml` |
| Bypass policy | Team Lead (+ Manager for high impact) | ADO PR |
| Approve Prod deploy | Prod Environment approver | ADO Pipeline run |
