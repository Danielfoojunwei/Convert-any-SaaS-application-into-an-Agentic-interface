# Full Integration Blueprint: Merge the Launch Workflow into Agent-See

## Executive direction

Yes — the right model is **not** to keep the end-to-end launch workflow as a completely separate universe from **Agent-See**. The right model is to make **Agent-See** the single top-level system, while exposing the launch and prompt-discovery pieces as both **modular sub-workflows** and a **full refresh path**.

That means a user should be able to run only the part they need, such as generating `llms.txt` or rebuilding the public `/agents` page, but when they re-run the full process, Agent-See should update the entire business surface in one coordinated pass.

## Recommended product model

The cleanest architecture is a **three-layer system**.

| Layer | Role | What the user experiences |
| --- | --- | --- |
| **Conversion layer** | Discovers and converts the business into an agent runtime | Existing `agent-see convert ...` behavior |
| **Launch layer** | Builds the public discovery, trust, and execution surfaces around that runtime | New `launch` commands and launch-state artifacts |
| **Sync layer** | Re-runs conversion-sensitive and launch-sensitive outputs together | One command that refreshes everything in one shot |

In other words, **Agent-See remains the product name and the main skill**, but it gains a new launch subsystem.

## What should happen during skill usage

The skill should support two modes of operation.

| Mode | User intent | Expected behavior |
| --- | --- | --- |
| **Modular mode** | “Only build this one thing” | Run only the requested sub-workflow and preserve the rest |
| **Full rerun mode** | “Refresh the whole system” | Rebuild conversion outputs, public assets, alignment checks, and maintenance artifacts together |

This is exactly the behavior you asked for: the user can run pieces separately, but if they rerun the broader system, **everything updates together**.

## Recommended CLI design

The current repository already has `convert`, `verify`, and `deploy`. The integration should extend the CLI rather than creating a second unrelated tool.

### Keep these commands

| Existing command | Keep? | Why |
| --- | --- | --- |
| `agent-see convert` | Yes | It is already the correct conversion boundary |
| `agent-see verify` | Yes | Proof validation remains useful and separate |
| `agent-see deploy` | Yes | Runtime deployment is already a natural post-conversion step |

### Add a new command group

Add a `launch` command group beneath `agent-see`.

| Proposed command | Purpose |
| --- | --- |
| `agent-see launch init` | Create or refresh the structured launch intake state |
| `agent-see launch build llms-txt` | Generate only `llms.txt` |
| `agent-see launch build agents-page` | Generate only the public `/agents` page draft |
| `agent-see launch build reference-layer` | Generate only the support/reference pages |
| `agent-see launch report` | Generate launch readiness report |
| `agent-see launch align` | Check public/runtime alignment |
| `agent-see launch update-register` | Generate maintenance update register |
| `agent-see launch sync` | Rebuild the full launch layer from the current intake and conversion outputs |
| `agent-see rerun` | Re-run conversion and then run `launch sync` so everything updates together |

This preserves the separation between **single-purpose tasks** and **full-surface refresh**.

## User experience model

The usage contract should be explicit.

| User says | System should do |
| --- | --- |
| “Just update the `/agents` page” | Run only `launch build agents-page` |
| “Regenerate `llms.txt`” | Run only `launch build llms-txt` |
| “Check if public docs still match runtime” | Run only `launch align` |
| “Rerun Agent-See for the new product flow” | Run conversion again, then run `launch sync` |
| “Refresh everything” | Run `agent-see rerun` and update all generated assets |

## Repository integration strategy

The GitHub repository should absorb the launch system as a **first-class subsystem**. Do not leave the automation scripts stranded only in a separate skill directory.

### Recommended repository layout

```text
src/agent_see/
  cli.py
  core/
  discovery/
  execution/
  generators/
  launch/
    __init__.py
    intake.py
    orchestrator.py
    sync.py
    alignment.py
    branches.py
    change_triggers.py
    models.py
  launch_generators/
    __init__.py
    llms_txt.py
    agents_page.py
    reference_layer.py
    launch_report.py
    update_register.py
  templates/
    launch/
      agents_page.md.j2
      llms.txt.j2
      coverage.md.j2
      limitations.md.j2
      pricing_eligibility.md.j2
      support_escalation.md.j2
      change_policy.md.j2

skills/
  agent-see/
    SKILL.md
    references/
      launch-workflow.md
      prompt-discovery-system.md
      public-surface-spec.md
      deployment-checklist.md
      ecommerce-branch.md
      saas-branch.md
      change-triggers.md
    templates/
      launch_intake.template.json
      launch_checklist.md
```

This turns the launch workflow into code inside the package and keeps the authoring guidance in the skill layer.

## What to move from the current launch skill into the repository

The current **agentic-business-launch** work should be split into two destinations.

| Current asset type | Move into repo code? | Move into Agent-See skill docs? |
| --- | --- | --- |
| Automation scripts | Yes | No |
| Structured state schema | Yes | Reference in skill |
| Prompt discovery system reference | No | Yes |
| Public surface specification | No | Yes |
| Deployment checklist | No, except checklist logic hooks | Yes |
| Ecommerce / SaaS branches | Partly; decision logic in code, detailed guidance in docs | Yes |
| Change-trigger mapping | Partly; trigger logic in code, human guidance in docs | Yes |

So the rule is simple: **deterministic execution belongs in the repo code; decision guidance belongs in the skill references**.

## How the integrated system should work

The flow should become state-driven.

### 1. One canonical launch state

The repository should standardize around one machine-readable file, for example:

```text
agent-output/launch/launch_intake.json
```

That file becomes the backbone for both modular and full runs.

It should hold the business identity, domain, business type, public pages, high-value workflows, conversion output paths, deployment target, login boundaries, approval-sensitive actions, support routes, pricing pages, documentation pages, and publication preferences.

### 2. One launch output area

All launch assets should live in a stable subtree inside the generated output.

```text
agent-output/
  mcp_server/
  AGENTS.md
  openapi.yaml
  agent_card.json
  proof/
  launch/
    launch_intake.json
    llms.txt
    agents.md
    reference_layer/
    launch_report.md
    launch_report.json
    alignment_report.md
    alignment_report.json
    update_register.md
```

This is important because it makes reruns predictable. The system always knows where to rebuild assets.

### 3. One orchestrator for selective vs full runs

A new orchestrator module should decide whether to run a single generator or all generators.

| Request type | Orchestrator behavior |
| --- | --- |
| Single asset requested | Run just that builder |
| Branch-specific refresh requested | Run the relevant builders and branch logic |
| Full launch sync requested | Run every builder in dependency order |
| Full rerun requested | Re-run conversion first, then run full launch sync |

## Dependency order for full refresh

When the user requests a full rerun, the system should not guess the order. It should use a fixed sequence.

| Order | Step | Why it must happen here |
| --- | --- | --- |
| **1** | Re-run conversion if requested | Runtime truth must refresh first |
| **2** | Refresh launch intake state | All downstream assets need current state |
| **3** | Rebuild `llms.txt` | Discovery file depends on canonical URLs |
| **4** | Rebuild public `/agents` page | Public execution layer depends on runtime truth |
| **5** | Rebuild reference layer | Trust and comparison surfaces depend on both state and public claims |
| **6** | Rebuild launch report | Report should describe the current generated state |
| **7** | Re-run alignment checks | Validation should happen after assets exist |
| **8** | Rebuild update register | Maintenance plan should reflect the newest accepted state |

This gives you the “update all at once if rerun” behavior you asked for.

## Skill-level integration model

The **Agent-See skill itself** should be expanded, not replaced.

### Recommended change to `skills/agent-see/SKILL.md`

The top-level skill should stop presenting Agent-See as only a converter. It should present Agent-See as a **two-stage operating system**:

| Stage | Description |
| --- | --- |
| **Stage 1: Convert** | Discover and convert the business surface into agent-executable runtime artifacts |
| **Stage 2: Launch** | Generate the public discovery, prompt, trust, and maintenance surfaces around that runtime |

The skill should then tell the agent to choose one of three operating modes.

| Operating mode | What it means |
| --- | --- |
| **Convert-only** | Use when the user only wants the runtime interface |
| **Launch-only** | Use when conversion exists and only public/business surfaces need updating |
| **Full rerun** | Use when the user wants all conversion and launch outputs refreshed together |

This lets the user run things separately during skill usage while keeping a unified rerun pathway.

## Recommended invocation rules inside the skill

The skill instructions should include a routing table like this.

| If the user asks for... | Skill should route to... |
| --- | --- |
| Runtime generation | `convert` |
| Runtime redeployment | `deploy` |
| `llms.txt` only | `launch build llms-txt` |
| `/agents` page only | `launch build agents-page` |
| Reference pages only | `launch build reference-layer` |
| Fresh readiness picture | `launch report` |
| Drift or mismatch detection | `launch align` |
| Ongoing maintenance planning | `launch update-register` |
| Everything refreshed | `rerun` |

## Concrete code changes to make in the repo

The integration should be implemented in the repository in a way that keeps current behavior stable.

### 1. Extend `src/agent_see/cli.py`

Add a `launch_app = typer.Typer()` subgroup and register launch subcommands there. Then add a top-level `rerun` command that wraps:

1. `convert`
2. `launch sync`
3. optional `deploy`
4. optional alignment check

### 2. Add launch state models

Create `src/agent_see/launch/models.py` with Pydantic models for:

| Model | Purpose |
| --- | --- |
| `LaunchIntake` | Canonical structured input |
| `PublicSurface` | `/agents`, docs, pricing, support, policy URLs |
| `WorkflowIntent` | High-value business workflows |
| `LaunchReport` | Machine-readable readiness output |
| `AlignmentReport` | Missing-link and mismatch output |
| `UpdateRegister` | Maintenance state and triggers |

### 3. Convert the standalone scripts into package modules

The current scripts should become importable package functions first, with CLI wrappers second.

| Current script | New package location |
| --- | --- |
| `init_launch_intake.py` | `src/agent_see/launch/intake.py` |
| `build_llms_txt.py` | `src/agent_see/launch_generators/llms_txt.py` |
| `build_agents_page.py` | `src/agent_see/launch_generators/agents_page.py` |
| `build_reference_layer.py` | `src/agent_see/launch_generators/reference_layer.py` |
| `build_launch_report.py` | `src/agent_see/launch_generators/launch_report.py` |
| `check_surface_alignment.py` | `src/agent_see/launch/alignment.py` |
| `build_update_register.py` | `src/agent_see/launch_generators/update_register.py` |

This is the most important code move because it makes them reusable from both the CLI and the skill.

### 4. Hook launch generation into `core/generator.py`

Do **not** force launch generation on every `convert` by default. Instead, give `generate_all(...)` an optional launch hook or a `with_launch: bool = False` pathway.

That keeps conversion lightweight while still allowing:

| Call pattern | Result |
| --- | --- |
| `agent-see convert` | Conversion only |
| `agent-see convert --with-launch` | Conversion plus full launch sync |
| `agent-see rerun` | Explicit full refresh of everything |

### 5. Extend output packaging

The repository already emits runtime-facing outputs like `AGENTS.md`, `agent_card.json`, `openapi.yaml`, and operational readiness artifacts. The launch system should generate sibling outputs under `agent-output/launch/` so the package becomes both **executable** and **discoverable**.

### 6. Add branch-aware logic

The orchestration layer should inspect the launch intake and activate the correct branch set.

| Business type | Branch logic |
| --- | --- |
| `saas` | Docs, onboarding, trust, auth-boundary checks |
| `ecommerce` | Catalog, price/availability, shipping/returns, comparison checks |
| `hybrid` | Run both sets and merge outputs |

### 7. Add rerun semantics

A rerun should treat the latest accepted output as baseline, then refresh all launch artifacts in place. This means the command should overwrite generated assets intentionally, not create ad hoc duplicates.

## What “update all at once if rerun” should mean technically

It should mean four specific behaviors.

| Behavior | Required implementation |
| --- | --- |
| **Deterministic rebuild** | Same output paths reused on rerun |
| **Dependency-aware refresh** | Assets rebuilt in fixed order |
| **Drift detection** | Alignment report regenerated after rebuild |
| **Baseline preservation** | Previous accepted state archived before overwrite |

Without those four behaviors, a rerun is just another generation pass, not a real synchronized refresh.

## Recommended repo-level command examples

```bash
# 1. Convert only
uv run agent-see convert https://example.com -o ./agent-output

# 2. Initialize or refresh launch state
uv run agent-see launch init --output ./agent-output/launch/launch_intake.json

# 3. Build one asset only
uv run agent-see launch build llms-txt --intake ./agent-output/launch/launch_intake.json
uv run agent-see launch build agents-page --intake ./agent-output/launch/launch_intake.json

# 4. Rebuild all launch assets from current state
uv run agent-see launch sync --intake ./agent-output/launch/launch_intake.json

# 5. Refresh everything together
uv run agent-see rerun https://example.com -o ./agent-output --with-launch
```

## Migration plan

The safest implementation path is incremental.

| Phase | What to do | Why this order works |
| --- | --- | --- |
| **1** | Move launch scripts into `src/agent_see/launch*` modules | Makes the logic importable |
| **2** | Add `launch` CLI subgroup | Exposes modular runs without breaking current commands |
| **3** | Add `launch sync` | Enables all-at-once launch refresh |
| **4** | Add `rerun` | Connects conversion refresh and launch refresh together |
| **5** | Expand `skills/agent-see/SKILL.md` | Aligns operator behavior with new repo capabilities |
| **6** | Add tests for modular and full rerun modes | Prevents regressions and partial-refresh bugs |

## Testing expectations

You should add integration tests for both separate runs and full reruns.

| Test case | What to prove |
| --- | --- |
| `launch build llms-txt` only | Does not mutate unrelated launch assets |
| `launch build agents-page` only | Rebuilds only the page draft and preserves state |
| `launch sync` | Rebuilds all launch artifacts in expected order |
| `rerun` | Rebuilds conversion outputs and launch outputs together |
| branch = `saas` | SaaS-specific artifacts and checks appear |
| branch = `ecommerce` | Ecommerce-specific checks and outputs appear |
| changed business logic | Rerun updates outputs and alignment report |

## Final recommendation

If your goal is **complete integration**, then the right answer is this:

1. **Keep Agent-See as the single parent system.**
2. **Absorb the launch automation into the Agent-See repository as package code.**
3. **Expand the Agent-See skill so it routes between convert-only, launch-only, and full-rerun modes.**
4. **Let users run sub-workflows separately.**
5. **When rerun is requested, refresh everything together into the same output tree.**

That gives you a system that is both **modular in normal use** and **synchronized on rerun**, which is the exact operating behavior you asked for.

## Suggested next implementation decision

The next concrete step should be to choose between these two implementation styles.

| Option | Recommendation |
| --- | --- |
| **A. Keep `agentic-business-launch` as a separate companion skill** | Good for experimentation, but not full integration |
| **B. Merge its automation and references into Agent-See as the official launch subsystem** | Best option if you want one GitHub repo, one skill family, and one rerun path |

If you want, I can do the next step and actually draft the **exact file-by-file GitHub diff plan** for the Agent-See repository, including which new Python modules, CLI commands, tests, and SKILL.md sections to add.
