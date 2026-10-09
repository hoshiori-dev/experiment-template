# Research Project Constitution

This charter binds every agent and every person working in this repository. The rules that follow it (the knowledge base
under `.agents/knowledge/`, the Spec Kit commands, the checks run by `just check`) derive from these five principles and
the governance section; where they conflict with this document, this document wins.

## Core Principles

### I. Evidence is traceable

A research conclusion counts only when a Formal Run supports it. Every Formal Run fixes four inputs before it starts: an
approved spec version (recorded by digest), a source commit that exists before execution, a frozen environment whose
manifest is committed with the source commit, and declared data with immutable versions. Its results live in one tracker
record that names the run and its source commit. Debug, smoke and exploratory runs are never evidence; a phenomenon seen
informally is cited only after a Formal Run reproduces it, and every conclusion in an Experiment README names the run
that supports it.

### II. Humans set direction and accept conclusions

Every Epic is approved by a maintainer before any exploration under it begins, and every synthesis becomes accepted
knowledge only when a human merges it. These two gates exist in every governance model and are never delegated to an
agent. Between the gates the governance model decides how much a human intervenes: per Experiment in human-led mode,
only at the gates in high-automation mode. The decision to leave the loop and write the report is made with a human
present.

### III. Rigor proportional to research risk

Research code serves iteration and evidence, not long-term maintenance; it owes no stable interfaces, backward
compatibility or general reuse. Engineering effort follows the importance of the result: informal runs need no
procedure, plans are rewritten as evidence arrives, and only runs that count as evidence follow the full Formal Run
procedure. Directories exist only when they hold real content, and shared libraries are extracted from finished
Experiments during a preparation phase, kept fine-grained.

### IV. One source of truth per fact

Git is the backbone of traceability. Whatever Git, the record files or the tracker can reliably derive is stored nowhere
else, and the project keeps no hidden state database. Epics and experiment issues exist only on the platform; the
rendezvous commit is recorded by branch ancestry; the commit a run used is the commit that added its record; the
Experiment ID names the spec directory, the experiment directory and the branch alike. Metrics live in the tracker,
conclusions in the Experiment README with the key numbers quoted and attributed to their run, and the project's status
is computed from the repository every time it is asked for.

### V. No silent degradation

A Formal Run never substitutes its execution environment, accelerator or dependency resolution on its own. When a
requested resource is unavailable, the run stops and reports; running under a different condition is a new decision,
recorded in a new run record. The same holds for checks: a failing check is fixed at its cause, never bypassed, weakened
or allow-listed to let content through.

## Governance

Two human gates frame every round: the Direction Gate, where a maintainer publishes an Epic by adding the label
`epic:approved` after creation, and the Acceptance Gate, where a human merges the synthesis pull request. Neither gate
can be removed or handed to an agent. An Epic is valid only while it is open, labeled after creation, and unedited since
the labeling; an invalid Epic stops the loop.

Protected paths are the shared parts of the repository: `docs/` (accepted experiment knowledge), `packages/` (shared
libraries) and the harness (agent entrypoints and knowledge, workflow definitions, permission tables, check scripts and
tests, task entrypoints, hook and scanner configuration, CI and platform templates, the dev container, the Experiment
starter template, the root workspace definition and its lock file). They change only in a preparation phase, and only a
human merges those changes; an agent may prepare them on a branch. During an experiment phase the only paths that change
are `specs/<id>/` and `experiments/<id>/`.

Agents never loosen their own constraints: they do not raise a budget, remove or weaken a check, relax a scanner, edit a
published Epic, or grant themselves platform write access. When a constraint blocks the work, the agent stops that
Experiment, records the reason, and reports to a human. Amendments to this constitution are themselves protected
changes: proposed on a branch, reviewed and merged by a human, with the version and amendment date updated below.

**Version**: 1.0.0 | **Ratified**: 2026-10-09 | **Last Amended**: 2026-10-09
