# Workflow Flowchart — Branch to Production

Visual companion to [`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md) and [`ADO-CICD-Adoption-Plan.md`](ADO-CICD-Adoption-Plan.md). Renders natively in the Azure DevOps wiki and on GitHub.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#EAF0FF','primaryBorderColor':'#3452C4','primaryTextColor':'#1E2430','lineColor':'#6B7280','fontFamily':'Segoe UI, sans-serif','clusterBkg':'#F6F4EF','clusterBorder':'#C9C2B4'}}}%%
flowchart TD

  subgraph PR["Pull Request Gate"]
    direction TB
    A[["checkout -b feature/&lt;name&gt;"]]:::git
    B("Commit changes"):::git
    C{"Pre-commit<br/>secret scan"}:::gate
    D["Push branch"]:::git
    E["Open PR → main"]:::git
    F{"Required checks:<br/>secret scan + bundle validate"}:::gate
    G("Code review"):::human
    H{"Approved?"}:::gate
    K{{"Team Lead:<br/>bypass + justification"}}:::bypass
    I[["Squash & merge to main"]]:::git
    J["Delete branch"]:::git

    A --> B --> C
    C -- secret found --> B
    C -- clean --> D --> E --> F
    F -- fails --> B
    F -- passes --> G --> H
    H -- changes requested --> B
    H -- approved --> I
    H -. emergency only .-> K -.-> I
    I --> J
  end

  J --> L["Pipeline triggers on main"]:::git

  subgraph CD["CI/CD Deployment — DevOpsBase template"]
    direction TB
    L --> M("Deploy to Dev<br/>(automatic)"):::auto
    L --> N("Deploy to QA<br/>(automatic)"):::auto
    N --> O{"QA succeeded?"}:::gate
    O -- no --> P["Stage fails —<br/>fix and re-merge"]:::bypass
    O -- yes --> Q{{"Waiting for approval<br/>Deploy_Prod"}}:::human
    Q -- reject --> R["Deployment stopped"]:::bypass
    Q -- approve --> S("Deploy to Prod"):::auto
    S --> T["Smoke test / monitor"]:::git
  end

  classDef auto fill:#EAF0FF,stroke:#3452C4,color:#1E2430,stroke-width:1.5px;
  classDef gate fill:#FFF7E6,stroke:#B8791A,color:#1E2430,stroke-width:1.5px;
  classDef human fill:#EAF7F0,stroke:#1F8A5F,color:#1E2430,stroke-width:1.5px;
  classDef git fill:#F2F0EA,stroke:#6B7280,color:#1E2430,stroke-width:1.2px;
  classDef bypass fill:#FBEAEA,stroke:#B23A3A,color:#1E2430,stroke-width:1.5px,stroke-dasharray: 4 3;
```

## Legend

| Shape | Meaning |
|---|---|
| Rounded box (blue) | Automatic pipeline stage — no human action |
| Diamond (amber) | Automated decision / gate check |
| Hexagon (green) | Human approval required |
| Rectangle (grey) | Git or local developer action |
| Dashed / red | Exception path — bypass, rejection, or failure |

## Reading it

- **Pull Request Gate** — a developer's change never reaches `main` without passing both the automated secret scan / bundle validation *and* a human reviewer, except through the dashed **bypass** path, which is restricted to the Team Lead and requires a documented justification (see [`GIT-WORKFLOW-GUIDE.md`](GIT-WORKFLOW-GUIDE.md) step 10).
- **CI/CD Deployment** — Dev and QA deploy **in parallel**; QA is not gated on Dev succeeding first. Production is gated on two independent conditions: QA must have succeeded, *and* a configured approver must sign off on the paused `Deploy_Prod` stage (see [`ADO-CICD-Adoption-Plan.md`](ADO-CICD-Adoption-Plan.md) section 5 and [`PLACEHOLDER-SETUP-GUIDE.md`](PLACEHOLDER-SETUP-GUIDE.md) #5).
