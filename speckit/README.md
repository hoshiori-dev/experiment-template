# Spec Kit preset and extension

This directory is the source of the project's research workflow for [Spec Kit](https://github.com/github/spec-kit). Spec
Kit provides the skeleton of three files per experiment (spec, plan, tasks) and the command mechanism. The meaning of
the files and the commands is the project's own and lives here.

| Directory    | What it is           | What it replaces or adds                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------ | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `preset/`    | Preset `research`    | Replaces the core templates `spec-template`, `plan-template`, `tasks-template` and the core commands `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.implement` with their research meaning: the spec is the fence around an Experiment, the plan is advisory, the tasks file is a rolling ledger. Replaces `speckit.analyze`, `.checklist`, `.clarify`, `.converge` and `.taskstoissues` with stubs that name the research command to use instead. |
| `extension/` | Extension `research` | Adds the research-loop commands `speckit.research.epic`, `.experiments`, `.approve`, `.run`, `.finish`, `.synthesize`, `.status`.                                                                                                                                                                                                                                                                                                                                |

`speckit.constitution` stays the upstream command; the project charter it maintains is
`.specify/memory/constitution.md`, edited there, not here.

## Installed copies

`.specify/` holds the installed copies (`.specify/presets/research/`, `.specify/extensions/research/`) and is committed,
so a fresh checkout needs no install. Only `.specify/feature.json`, the per-checkout pointer to the current experiment,
stays out of Git.

Spec Kit installs one agent integration, Claude: every command is materialized as `.claude/skills/speckit-*/SKILL.md`
(dots in command names become hyphens, so `speckit.research.run` is `/speckit-research-run`). Codex reads
`.agents/skills/`, where each `speckit-*` entry is a symlink to the same skill under `.claude/skills/`. OpenCode reads
`.claude/skills/` directly.

## Edit

The installed copies are generated. After editing anything under `speckit/`, run `just speckit-install` and commit
`speckit/` together with the regenerated files under `.specify/` and `.claude/skills/speckit-*/`. The symlinks under
`.agents/skills/` keep working as long as the skill names do; a renamed or added command needs a new symlink there
(`ln -s ../../.claude/skills/<name> .agents/skills/<name>`). All of these are protected paths: changes are prepared on a
branch during a preparation phase and merged by a human.
