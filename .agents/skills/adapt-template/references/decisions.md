# Decisions

The catalogue of what can be decided about the harness: options, what each costs, how to read the current value
from the repository, and where the value is stated. It describes options only; it never says which option a
project uses. "Stated in" is a starting point for the search, not a complete list: files move, so confirm each
entry and grep for the old value.

"The agent permission files" are the ones listed in `.agents/knowledge/tooling.md` (Agent framework permission files),
configuration and rule files alike. "Opens" names the decisions a change of this one puts back on the table.

Every decision is the owner's. The agent lays out status, options and costs, and never changes a setting to widen
its own reach.

## Order

Ask in this order; a decision waits until the ones it depends on are settled.

1. Project identity, owner handle, hosting platform, repository visibility, governance model.
2. External writes (needs platform and governance), publishing standard and commit address (need visibility),
   agent attribution, protected paths, branch structure.
3. Execution environment, tracker, then the dependency baseline (needs the execution environment).
4. Epic-level hard cap, approval-label automation, and anything the earlier answers opened.

## Catalogue

### Project identity

Name, objective, and the language of human-facing documents. Owner-only facts; ask bare.
Read from: `README.md` title and first section; `.specify/memory/constitution.md`.
Stated in: `README.md`, its mirror (`README.zh.md` or the mirror in the chosen language),
`.specify/memory/constitution.md` (keep the five principles unless the owner changes the design).

### Owner handle

The platform login that reviews protected paths. Owner-only fact.
Read from: `.github/CODEOWNERS`.
Stated in: `.github/CODEOWNERS` only. Replace every occurrence before code-owner review is enabled.

### Hosting platform

Options: GitHub; GitLab and others (see backends.md). Cost of leaving GitHub: the scripts that query the platform and the permission tables are rewritten.
Opens: external writes, approval-label automation, commit address.
Read from: AGENTS.md "Current settings" (Platform); the command `scripts/_gh.py` calls.
Stated in: AGENTS.md, `README.md`, `.agents/knowledge/tooling.md`, `scripts/_gh.py`, `scripts/epic_status.py`,
`scripts/spec_approval.py`, `.github/`, the Spec Kit commands under `speckit/`, the agent permission files.

### Repository visibility and publishing standard

Options: public with the public-repository standard (mechanical scan plus agent read-through, extended personal
data rules); private in a controlled environment (keep the secret scan and the no-secrets rule, drop the extended
personal-data rules and the read-through). Going public later means reviewing the whole history first.
Opens: commit address.
Read from: AGENTS.md "Current settings" (Publishing standard); the rule list in `.gitleaks.toml`; the platform
(`gh repo view --json visibility`).
Stated in: AGENTS.md, `README.md`, `.agents/knowledge/governance.md` (Confidentiality),
`.agents/knowledge/publishing.md`, `.gitleaks.toml`, the skill under `.agents/skills/` that performs the outbound review.

### Governance model

Options: human-led (humans create experiment issues, a human approves each spec and merges each experiment pull
request; steady and slow); high-automation (the agent plans Experiments under a published Epic, an independent
agent approves specs, the agent merges experiment pull requests; needs platform tools and protection first). The model
also fixes who applies the spec approval label.
Opens: external writes, approval-label automation.
Read from: AGENTS.md "Current settings" (Governance model); the column marked current in
`.agents/knowledge/governance.md` (Two governance models).
Stated in: AGENTS.md (Current settings, Procedures), `README.md`, `.agents/knowledge/governance.md`, the agent permission files, the Spec Kit commands that branch on the model.

### External writes

Options: on (the agent pushes its own branches, opens issues and pull requests, comments, labels); off (the agent
drafts to `.local/drafts/` and a human posts). Turning it on needs the platform prerequisites in
`.agents/knowledge/tooling.md` first, or "protected paths are merged only by humans" has nothing enforcing it.
Read from: AGENTS.md "Current settings" (External writes); whether the permission files allow `git push` and the
platform write commands.
Stated in: AGENTS.md, `README.md`, `.agents/knowledge/governance.md` (External writes),
`.agents/knowledge/publishing.md`, `.claude/settings.json`, `.codex/rules/`, `opencode.json`.

### Agent attribution

Options: forbidden (instruction, framework setting, commit hook); allowed (remove the `attribution` block in
`.claude/settings.json`, relax the hook; the responsibility argument in `governance.md` still applies).
Read from: the `attribution` block in `.claude/settings.json`; the attribution check in
`scripts/check_commit_message.py`.
Stated in: AGENTS.md (Always), `.agents/knowledge/governance.md` (Attribution), `README.md`,
`.claude/settings.json`, `scripts/check_commit_message.py` and its tests.

### Commit address

Options: platform noreply only (fits public hosting); open (fits internal deployments).
Read from: `REQUIRE_NOREPLY_AUTHOR` in `scripts/check_commit_message.py`; the email rule in `.gitleaks.toml`.
Stated in: those two files, `.agents/knowledge/structure.md` (Commit messages).

### Protected paths

Options: `docs/`, `packages/` and the harness at least; more may be added. Removing a harness path lets the agent
edit its own rules, so that is never proposed by the agent.
Read from: `.github/CODEOWNERS`; `scripts/check_branch_scope.py`.
Stated in: those two files, AGENTS.md (Always, Layout), `.agents/knowledge/governance.md` (Protected paths).

### Branch structure

Any structure works that keeps the four requirements in `.agents/knowledge/structure.md` (Branches).

| Structure                       | How                                                                                                                  | Fits                                                      | Cost                                                                                    |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| mainline + experiment branches  | each Experiment branches from `main`, returns with a merge commit                                                    | a small team in one repo, or one person with agents       | `main` moves during experimentation; the freeze rests on protected paths and convention |
| fork workflow                   | each researcher forks, branches in the fork, opens PRs to the main repo; everyone syncs at preparation               | several researchers, or contributors without write access | Epics and experiment issues exist only in the main repo                                 |
| one integration branch per Epic | branch at the end of preparation; experiments branch from and return to it; merged to `main` at the next preparation | a visible branch point for the frozen environment         | one more layer, alive for a whole round                                                 |

Read from: `.agents/knowledge/structure.md` (Branches).
Stated in: that section, `scripts/check_branch_scope.py`, `scripts/budget.py` and `scripts/research_status.py`
(they read run branches), the Spec Kit commands that create branches.

### Execution environment

Options and what stays fixed: backends.md.
Read from: AGENTS.md "Current settings" (the row is labelled as an example because the boundary, not the tool, is the
rule; its value is still the one in use); `template/experiment/`.
Stated in: AGENTS.md, `README.md`, `.agents/knowledge/evidence.md` (the examples), `template/`,
`speckit/extension/commands/speckit.research.run.md`.
Opens: dependency baseline.

### Tracker

Options and what stays fixed: backends.md.
Read from: AGENTS.md "Current settings"; `scripts/tracker_lookup.py`; the `tracker` block of existing run records.
Stated in: AGENTS.md, `README.md`, `.agents/knowledge/evidence.md`, `scripts/tracker_lookup.py` and the scripts that
import it, `template/run-record.yaml`, `speckit/extension/commands/speckit.research.run.md`.
Opens: dependency baseline (the tracker's client library); external writes when the tracker is remote.

### Dependency baseline

What every Experiment starts from: the dependency declaration and lock, the base image, tool versions. Options:
empty (each Experiment adds what it needs, later ones reuse earlier locks); filled with the project's usual stack
(Experiments share one installed environment from the first run). Changing a filled baseline later makes new
Experiments differ from finished ones, which is a variable in every comparison across them.
Read from: `template/experiment/pyproject.toml`, `template/experiment/uv.lock`, the `FROM` line of
`template/experiment/Dockerfile`.
Stated in: `template/experiment/`, `template/README.md`.

### Epic-level hard cap

Options: checked by the approver; machine-enforced (a script reads every Experiment's spec cap and the usage
comments on issues).
Read from: whether a script under `scripts/` sums budgets across the Experiments of an Epic.
Stated in: `.agents/knowledge/governance.md` (Budget), `speckit/extension/commands/speckit.research.approve.md`,
`README.md`.

### Approval-label automation

Options: off (convention); on (a workflow removes `spec:approved` when `specs/<id>/spec.md` changes and rejects
labels applied by the author; mind the permissions of pull requests from forks).
Read from: whether a workflow under `.github/workflows/` handles the label.
Stated in: `.agents/knowledge/governance.md` (Spec approval), `README.md`, the workflow itself when it exists.

## Not decisions

These hold in every adaptation: a human publishes every Epic and a human merges every synthesis; the shared part
changes only in preparation and is merged by humans; budget caps are set by humans; the agent never loosens its
own rules and checks; the five forbidden content classes and the three confidentiality rules; English for code and
agent-facing files. The budget unit and "unlimited" are written in each Epic, not in a file.
