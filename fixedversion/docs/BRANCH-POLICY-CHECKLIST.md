# Branch policy setup checklist (ADO UI — not enforceable from git alone)
#
# Project Settings → Repositories → main → Policies
#
# [ ] Minimum number of reviewers: 1 or 2
# [ ] Allow requestors to approve their own changes: OFF
# [ ] Check for comment resolution: Optional → Required (recommended)
# [ ] Build Validation → azure-pipelines-ci-pr.yml → Required + auto trigger
# [ ] Build Validation → azure-pipelines-ci-secret-scan.yml (optional extra) → Required
# [ ] Limit merge types → prefer Squash merge
# [ ] Bypass policy permission: Team Leads / admins only
#
# Pipelines → Environments → <PROD_ADO_ENVIRONMENT>
# [ ] Approvals: tech lead / release owner
# [ ] Optional: business hours gate
#
# Owner: __________________  Date enabled: __________
