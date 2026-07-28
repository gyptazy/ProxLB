# CP-SAT Solver (Optional)

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Configuration](#configuration)
    1. [Configuration Reference](#configuration-reference)
    2. [Shadow Mode (default)](#shadow-mode-default)
    3. [Active Mode](#active-mode)
6. [Logging and Reports](#logging-and-reports)
7. [Interaction with ProxLB Constraints](#interaction-with-proxlb-constraints)
8. [Operational Notes](#operational-notes)


## Overview

ProxLB optionally integrates a **CP-SAT solver** (Google OR-Tools) that replaces the built-in greedy
load balancer with a mathematically optimal placement engine.  The solver finds the assignment of
VMs and containers to nodes that minimises the peak resource imbalance across the cluster while
respecting all configured constraints (affinity, anti-affinity, pinning, node reservations, CPU
overcommit limits, and maintenance modes).

The solver runs in one of two modes:

| Mode | Description |
|------|-------------|
| `shadow` *(default)* | Solver computes an optimal plan in parallel with ProxLB. Migrations are still performed by ProxLB's greedy algorithm. Results are written to a JSONL log and an HTML report for comparison. |
| `active` | Solver drives all migrations. Each step is verified against the live Proxmox API and, if a migration fails, the solver re-solves from the updated cluster state with the failed VM pinned to its current node. |

In both modes the solver is **completely optional** — if the `proxlb-solver` package is not
installed, ProxLB logs a warning and continues with its normal greedy algorithm unchanged.


## How It Works

### Shadow mode

```
ProxLB greedy run
       │
       ├─► solver runs in parallel, reads cluster state
       │       │
       │       └─► writes JSONL events + HTML report
       │
       └─► Balancing() executes ProxLB's own plan via the Proxmox API
```

After every run, a structured JSONL file is written to `log_dir` containing:
- `proxlb_action` — one entry per migration ProxLB planned
- `cluster_state` — node capacities and current VM placement snapshot
- `constraint` — every affinity / anti-affinity / pin / ignore rule the solver recognised
- `solver_run` — solver status, migration count, load gap, wall time
- `plan_step` — one entry per migration in the solver's ordered plan
- `compare` — per-VM comparison (`agree` / `differ` / `solver_only` / `proxlb_only`)
- `infeasible` — which VMs block a valid solution (when the solver cannot find a placement)
- `proxlb_executed` — appended after Balancing() completes; `dry_run=True` when `--dry-run` was used

### Active mode

```
ProxLB greedy run (produces initial cluster state)
       │
       └─► solver produces ordered migration plan (Kahn's algorithm)
               │
               ├─► step 1: Balancing() migrates VMs in this step
               │       │
               │       ├─► verify via Proxmox cluster/resources API
               │       │
               │       ├─► success → advance to step 2
               │       │
               │       └─► failure → pin failed VMs, re-solve, restart plan
               │
               ├─► ... repeat for remaining steps ...
               │
               └─► remainder (PVE-deferred / unresolvable cycles / persistent failures)
                       └─► original ProxLB targets restored, Balancing() handles them
```

The migration plan is topologically ordered so that circular dependencies (VM-A needs node-1
which requires VM-B to move first) are resolved with temporary parking moves.  Steps that are
independent of each other are flagged `parallel: true` in the plan and can be migrated
concurrently.


## Requirements

| Dependency | Version | Notes |
|------------|---------|-------|
| `proxlb-solver` | any | Pulls in `ortools` automatically |
| `ortools` | ≥ 9.x | Included as a transitive dependency |
| Python | ≥ 3.11 | Same as ProxLB 2.0 |

The solver package is separate from the main ProxLB package and is installed as a dependency.


## Configuration

Add a `solver:` block to your `proxlb.yaml` (see also `config/proxlb_example.yaml`):

```yaml
solver:
  enable: True
  mode: shadow            # 'shadow' (observe only) or 'active' (solver drives migrations)
  log_dir: /var/log/proxlb/solver
  timeout_seconds: 30     # CP-SAT wall-clock time limit per solve
  use_reservations: True  # honour node_resource_reserve entries from the balancing section
  active_step_retries: 3  # max re-solve attempts on migration failure (active mode only)
  fallback_to_greedy: True  # fall back to greedy Balancing() when the solver cannot place VMs
```

### Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enable` | bool | `False` | Enable the solver integration. When `False`, ProxLB will neither use `shadow` mode nor `active` mode. |
| `mode` | string | `shadow` | `shadow` — observe only; `active` — solver drives migrations. |
| `log_dir` | string | `/var/log/proxlb/solver` | Directory for JSONL run logs and HTML reports. Created automatically if absent. The user running ProxLB must have write access (see [Log directory permissions](#logging-and-reports)). |
| `timeout_seconds` | float | `30.0` | Wall-clock time limit given to the CP-SAT solver per solve (initial solve and each re-solve in active mode). |
| `use_reservations` | bool | `True` | When `True`, memory reservations defined in `balancing.node_resource_reserve` are applied as hard constraints in the solver (capacity is reduced by the configured GB). |
| `active_step_retries` | int | `3` | Maximum number of re-solve attempts in active mode. After this many failures the remaining VMs are handed back to ProxLB's Balancing() when `fallback_to_greedy` is `True`. |
| `fallback_to_greedy` | bool | `True` | In active mode, fall back to ProxLB's greedy `Balancing()` when the solver returns no feasible plan (`INFEASIBLE`), active execution fails, or retries are exhausted. Set to `False` for fail-closed, solver-only behaviour. |

### Shadow mode (default)

Shadow mode requires no changes beyond enabling the solver:

```yaml
solver:
  enable: True
  mode: shadow
  log_dir: /var/log/proxlb/solver
```

ProxLB runs as usual. After the greedy algorithm completes, the solver calculates its own optimal
plan and writes a JSONL log.  No migrations are changed.  The report tool then renders an HTML
comparison showing where solver and ProxLB agreed or differed and what the projected node load
would look like under each plan.

### Active mode

```yaml
solver:
  enable: True
  mode: active
  log_dir: /var/log/proxlb/solver
  timeout_seconds: 60
  active_step_retries: 3
  fallback_to_greedy: False  # fail closed: do not migrate when the solver cannot find a safe plan
```

In active mode the solver replaces ProxLB's migration execution.  If a migration fails (verified
via the Proxmox `cluster/resources` API), the failed VM is pinned to its current node and the
solver re-solves from the updated cluster state.  This repeats up to `active_step_retries` times.
If the re-solve is infeasible or retries are exhausted, the remaining VMs are handled by ProxLB's
own Balancing() call when `fallback_to_greedy` is `True` (default).

If the solver raises an unexpected exception during active execution, ProxLB logs a warning and
falls back to its greedy Balancing() when `fallback_to_greedy` is `True`. With
`fallback_to_greedy: False`, no greedy migrations are issued in these cases.


## Logging and Reports

Every ProxLB run with the solver enabled creates a timestamped JSONL file in `log_dir`:

```
/var/log/proxlb/solver/solver_run_20260310_140000.jsonl
```

Each line is a JSON object with an `event` field and a `ts` (ISO-8601 UTC timestamp).

### Generating HTML reports

The `proxlb-solver-report` command (installed with the `proxlb-solver` package) renders a
self-contained HTML report from the log directory:

```bash
proxlb-solver-report \
    --log-dir /var/log/proxlb/solver \
    --output-dir /var/www/html/solver-report
```

The report contains:
- **Index page** — overview of all runs: date, solver status, migration counts (solver vs. ProxLB),
  load gap, solve time.
- **Detail page per run** — solver plan with ordered migration steps, node load bars (before/after
  applying the solver plan), constraint list, ProxLB plan comparison table, and (in active mode)
  the sequential execution log with per-step success/failure and any re-solve passes.


## Interaction with ProxLB Constraints

The solver reads and enforces all constraints that ProxLB recognises:

| Constraint source | Solver behaviour |
|-------------------|-----------------|
| `plb_affinity_*` tags | Hard affinity constraint — all tagged VMs must share a node |
| `plb_anti_affinity_*` tags | Hard anti-affinity constraint — tagged VMs must be on different nodes |
| Proxmox native HA affinity/anti-affinity rules | Translated to the same hard constraints as PLB tags |
| Resource pool affinity / anti-affinity (`balancing.pools`) | Same as tag-based rules |
| `plb_pin_<node>` tags | VM is restricted to the listed node(s) |
| Pool pin rules | Same as tag-based pinning |
| `plb_ignore_*` tags | VM is excluded from solver placement; its current node is treated as fixed |
| `balancing.node_resource_reserve` | Reduces usable node capacity by the configured GB (when `use_reservations: True`) |
| `maintenance_nodes` | Node is excluded as a migration target |
| `balancing.cpu_overcommit` | Maximum ratio of vCPUs to physical cores per node |
| `balancing.max_node_inflow` | Maximum number of VMs that may be migrated onto any single node per run |

When the solver cannot find a placement that satisfies all hard constraints (e.g. anti-affinity on
a single-node cluster), it reports the blocking VMs in an `infeasible` JSONL event and returns
`None`.  In shadow mode ProxLB continues with its own plan; in active mode ProxLB falls back to
its greedy Balancing() when `fallback_to_greedy` is `True` (default).


## Operational Notes

- **ProxLB 2.0 only.** The solver integration requires ProxLB 2.0's Pydantic-based data models.
  It cannot be used with ProxLB 1.x.

- **Dry-run support.** When ProxLB is started with `--dry-run`, the solver still runs and writes
  its log, but the `proxlb_executed` event records `dry_run: True` and no migrations are sent to
  the Proxmox API.

- **Log directory permissions.** The directory specified in `log_dir` is created automatically on
  first run.  Ensure the user running ProxLB has write access.  If the directory cannot be created,
  a warning is logged and the solver is skipped for that run.

- **Solve time vs. cluster size.** The CP-SAT solver is exact: it finds the provably optimal
  solution.  For large clusters (50+ nodes, 500+ VMs) with many constraints, it may not reach
  optimality within `timeout_seconds` — it will return the best solution found so far.  Increase
  `timeout_seconds` if you consistently see non-OPTIMAL status in the logs.

- **Active mode and PVE HA.** VMs managed by Proxmox HA that cannot be placed by the solver (e.g.
  due to unresolvable dependency cycles) are handed back to ProxLB Balancing() with their original
  `node_target`, allowing PVE HA to handle them through its own mechanisms.
