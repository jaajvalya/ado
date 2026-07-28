# Git & Azure DevOps Workflow Guide

Step-by-step instructions for the day-to-day Git/Azure DevOps (ADO) workflow on this repo, plus who is expected to do what.

**Part 1** is the operational how-to (commands + ADO UI steps) — use this as the reference regardless of role.
**Part 2** maps those steps to each audience (Developer, Team Lead, Manager, Approver) so everyone knows their responsibility and limits.

This guide assumes `main` is protected by branch policies (required reviewers + the secret scan build validation from [`SECRETS-POLICY.md`](SECRETS-POLICY.md)) and that `PROD` deployments go through the environment approval gate described in [`ADO-CICD-Adoption-Plan.md`](ADO-CICD-Adoption-Plan.md).

---

## Part 1 — Step by step

### 1. Clone the repo

```bash
git clone https://<org>@dev.azure.com/<org>/<project>/_git/<repo>
cd <repo>
```

Use the exact clone URL from **ADO → Repos → Clone**. Do this once per machine.

### 2. Create a branch

Always branch off an up-to-date `main`.

```bash
git checkout main
git pull origin main
git checkout -b feature/<short-description>
# examples: feature/sample-etl-job, bugfix/dev-target-path, hotfix/qa-token-refresh
```

Naming convention: `feature/…`, `bugfix/…`, `hotfix/…` — keep it short and specific; avoid personal names or ticket numbers alone.

### 3. Commit changes

```bash
git add <specific files>      # avoid `git add .` — review what's staged first
git status                    # confirm nothing unintended is staged
git commit -m "Short, specific summary of the change"
```

If [`.pre-commit-config.yaml`](.pre-commit-config.yaml) is installed (see [`SECRETS-POLICY.md`](SECRETS-POLICY.md)), the commit will be blocked automatically if gitleaks detects a secret. Do not bypass this with `--no-verify` — fix the root cause instead.

### 4. Push the branch

```bash
git push -u origin feature/<short-description>
```

`-u` only needed on first push of that branch; after that, `git push` alone works.

### 5. Pull / keep your branch current

Before pushing new work, or if your PR shows conflicts, bring `main` into your branch:

```bash
git checkout main
git pull origin main
git checkout feature/<short-description>
git merge main          # or: git rebase main, if your team prefers linear history
# resolve any conflicts, then:
git push
```

### 6. Create a Pull Request (PR)

- ADO → **Repos → Pull Requests → New Pull Request**
- Source: your branch → Target: `main`
- Fill in a clear title/description: what changed and why
- Link the related work item if one exists
- Add required/suggested reviewers
- Create the PR — this automatically triggers the required build validation (secret scan; and, once wired up, `databricks bundle validate` — see [`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml))

### 7. Review and Approve

Reviewers open the PR → **Files** tab:

- Read the diff, leave inline comments on specific lines for anything unclear or risky
- Check the required pipeline checks are green (build validation, secret scan)
- Vote using the button in the top right of the PR:
  - ✅ **Approve** — good to merge
  - ✅ **Approve with suggestions** — minor non-blocking notes
  - ✏️ **Wait for author** — changes requested, blocks merge until addressed
  - ❌ **Reject** — do not merge as-is
- A PR cannot complete until it has the number of approvals configured in the branch policy (typically 1–2), from people other than the author — self-approval should be disabled in policy.

### 8. Merge

Once required approvals and checks pass, click **Complete** on the PR. ADO offers merge strategies:

| Strategy | What it does | When to use |
|---|---|---|
| **Squash and merge** | Collapses all commits on the branch into a single commit on `main` | **Default for feature/bugfix branches** — keeps `main` history clean and readable, one commit per PR |
| Merge (no fast-forward) | Keeps all individual commits plus a merge commit | When commit-by-commit history genuinely matters (rare here) |
| Rebase and fast-forward | Replays commits onto `main` with no merge commit | Only if the team has standardized on linear history and commits are already clean |

To squash & merge: in the **Complete pull request** dialog, set **Merge type** to **Squash commit**, edit the resulting commit message if needed (summarize the whole PR), then **Complete merge**.

### 9. Delete the branch

ADO prompts **"Delete source branch after merge"** in the same completion dialog — check it. If you merged without checking it:

```bash
git push origin --delete feature/<short-description>
git branch -d feature/<short-description>     # delete local copy too
```

Don't delete a branch that hasn't merged, or that another PR still targets, without confirming with its author first.

### 10. Bypass approval (exception path — use sparingly)

Bypassing branch policy skips required reviewers/checks and completes the PR immediately. It requires the **"Bypass policies when completing pull requests"** permission, which should be restricted to a small group (Team Lead / repo admins) — not granted broadly.

- In the **Complete pull request** dialog, if you have this permission, an option appears to complete despite unmet policies
- **Only for genuine emergencies** (e.g., a production-breaking hotfix where waiting for review would extend an outage) — never as a convenience to skip review
- Always leave a PR comment stating *why* the bypass was necessary, before or immediately after completing it — this is the audit trail
- Follow up with a normal retrospective review of the change after the fact; a bypassed PR should still get eyes on it, just after the fact instead of before

### 11. Approving a Production deployment (separate from PR approval)

This is a **different gate** from PR review — it's the ADO Environment approval on the `PROD` stage of [`azure-pipelines-databricks-bundles.yml`](azure-pipelines-databricks-bundles.yml) (see [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #5). A PR can be merged to `main` and still not deploy to Prod until this is approved separately.

- When a pipeline run reaches the `Deploy_Prod` stage, it pauses in **"Waiting for approval"**
- Configured approver(s) get a notification; go to the pipeline run → the pending Prod stage shows **Review** or **Approve/Reject**
- Approve only after confirming: QA stage succeeded, the change was reviewed in its PR, and (for scheduled/regulated changes) any required change record exists
- Rejecting stops the deployment; it does not affect the merged PR or the `main` branch

---

## Part 2 — By audience

### Developer

Owns steps **1–6 and 9**. Cannot self-approve or bypass policy (unless separately granted, which is atypical for this role).

1. Clone the repo once ([step 1](#1-clone-the-repo))
2. Create a feature/bugfix branch off current `main` for every change ([step 2](#2-create-a-branch))
3. Commit in small, reviewable chunks with clear messages ([step 3](#3-commit-changes))
4. Push and open a PR ([steps 4, 6](#4-push-the-branch))
5. Keep the branch current with `main` if it drifts or conflicts appear ([step 5](#5-pull--keep-your-branch-current))
6. Respond to review comments (step 7) with new commits — no force-push required, just push additional commits so reviewers can see the diff since their last review
7. Once approved, complete the merge yourself if your org allows author-merge (or hand off to the Approver/Team Lead), using **squash and merge** ([step 8](#8-merge)) and deleting the branch ([step 9](#9-delete-the-branch))
8. Never use `--no-verify` to skip the local secret-scan hook — fix the flagged issue instead ([`SECRETS-POLICY.md`](SECRETS-POLICY.md))

### Team Lead

Owns branch policy configuration, most PR reviews/approvals, and is typically the one holding **bypass** permission.

1. Configure and maintain branch policies on `main` (required reviewer count, required build validation checks, "no self-approval") — one-time/admin, ADO **Project Settings → Repositories → main → Policies**
2. Perform code reviews (step 7) with a focus on design/architecture correctness, not just style
3. Decide/confirm merge strategy per PR — **squash and merge** is the default; only override for a specific documented reason
4. Hold **bypass approval** permission ([step 10](#10-bypass-approval-exception-path--use-sparingly)) for genuine emergencies only, and ensure every bypass has a documented reason and a follow-up review
5. Be one of the configured approvers on the `PROD` ADO Environment where appropriate ([step 11](#11-approving-a-production-deployment-separate-from-pr-approval))
6. Periodically audit merged PRs for policy compliance (were required approvals real, was anything bypassed without justification)

### Manager

Generally not hands-on with day-to-day Git operations; owns process oversight and exception authorization at a level above the Team Lead.

1. Does not typically clone/branch/commit/push/merge directly — this role is about ensuring the *process* in Part 1 is followed, not executing it
2. Jointly authorizes **bypass approval** for business-critical situations alongside the Team Lead when the bypass has broader impact (e.g., affects a client-facing deadline or a Prod incident) — the Team Lead still performs the technical bypass, the Manager provides the business sign-off referenced in the PR comment
3. Reviews recurring compliance signals: how often bypass is used, whether the required-approval and secret-scan policies stay enabled and enforced (not quietly disabled under deadline pressure)
4. Is the escalation point when a Developer/Approver disagreement on a PR can't be resolved between them
5. Ensures new team members are granted the *correct* ADO permission level (Developer ≠ Team Lead ≠ bypass-capable) rather than defaulting everyone to admin for convenience

### Approver

Covers two distinct responsibilities — a person may hold one or both:

**A. PR Approver** (branch policy reviewer)
1. Review the diff for correctness, security (no secrets — cross-check against [`SECRETS-POLICY.md`](SECRETS-POLICY.md)), and adherence to the bundle structure conventions in [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md)
2. Confirm required automated checks are green before voting Approve — don't approve around a red build validation
3. Vote per [step 7](#7-review-and-approve); use "Wait for author" rather than a vague comment if something must change before merge
4. Never approve your own PR; if you're both author and the only available reviewer, escalate to the Team Lead rather than waiting for the policy to be bypassed

**B. Prod Deployment Approver** (ADO Environment approval)
1. Distinct from PR approval — this happens at deploy time, not at merge time ([step 11](#11-approving-a-production-deployment-separate-from-pr-approval))
2. Verify the QA stage succeeded and the underlying PR was properly reviewed (not bypassed) before approving the Prod stage
3. Reject (rather than sit on) a Prod approval if something looks wrong — a rejected stage is easy to re-trigger once fixed; an approved-then-broken Prod deploy is not

---

## Quick reference

| Action | Who normally does it | Where |
|---|---|---|
| Create branch, commit, push | Developer | Local Git |
| Open PR | Developer | ADO Repos |
| Review & vote Approve | Approver / Team Lead | ADO PR |
| Choose squash & merge, complete PR | Developer or Approver/Team Lead (per org convention) | ADO PR |
| Delete branch | Whoever completes the PR (checkbox) or Developer after | ADO PR / Git |
| Bypass policy | Team Lead (technical action), Manager (business sign-off for high-impact cases) | ADO PR |
| Approve Prod deployment | Approver (Prod Environment approver) | ADO Pipeline run |
