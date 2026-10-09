---
name: harness-checkup
description: >
  Periodic entropy check of the harness, run at the rendezvous before synthesis or when the owner asks for a harness
  audit. Finds stale paths and commands in AGENTS.md and the knowledge files, dead just recipes, meanings stated in
  more than one place, knowledge files no pointer reaches, rules that could have a mechanical check but have none,
  and rules thicker than their job. Writes a report to .local/drafts/ and proposes fixes on a separate branch, never
  on the synthesis branch.
license: MIT
compatibility: Requires a git working tree with just, uv and deno available.
---

# Harness checkup

Role: auditor of the files that constrain and guide agents. Goal: a report of what drifted and a branch with proposed
fixes, both for a human to act on. The harness is a protected path: this skill changes nothing on `main`, on the
synthesis branch, or on any experiment branch.

## Procedure

1. **Fix the baseline.** Note the rendezvous commit (`git rev-parse HEAD` on `main`) and the date. Create the report at
   `.local/drafts/harness-checkup-<YYYY-MM-DD>.md` with the commit hash in its first line. Done when the file exists.
2. **Stale paths and commands.** For every path, recipe, script and command named in `AGENTS.md`,
   `.agents/knowledge/*.md`, `.agents/skills/*/SKILL.md` and the Spec Kit command files under `speckit/`, confirm it
   exists (`test -e`, `just --list`, `ls scripts/`). Done when each name is either confirmed or listed as stale with the
   file and line that names it.
3. **Dead recipes and scripts.** Each `just` recipe and each `scripts/*.py` is named by at least one of `AGENTS.md`, a
   knowledge file, a skill, a Spec Kit command, `.pre-commit-config.yaml` or `.github/workflows/`. List the ones nothing
   names.
4. **Duplicated meanings.** Find a rule, list or value stated in more than one file (protected paths, label names,
   budget arithmetic, forbidden content classes, the run record schema, command names). For each, name the file that
   should be the single source and the copies to turn into pointers.
5. **Unreachable knowledge.** Each `.agents/knowledge/*.md` and each skill is named, with a when-to-read trigger, by
   `AGENTS.md` or by another file `AGENTS.md` reaches. List the files no pointer reaches and the pointers whose trigger
   is vague ("see X for details").
6. **Rules without a check.** For each rule in the knowledge files that a script or hook could verify mechanically (path
   shape, enum values, branch scope, required fields, naming), check whether one exists in `scripts/` or
   `.pre-commit-config.yaml`. List the candidates with the check that would cover them.
7. **Thick rules.** Flag passages that restate a rule, explain what the environment already answers, prescribe how to
   build or run an experiment, or carry no behaviour change for the weakest model reading them. Quote by file and line,
   propose the shorter form.
8. **Run the checks.** `just check` and `just status`; record failures as findings.
9. **Write the report.** Sections in this order: Baseline, Stale, Dead, Duplicated, Unreachable, Unchecked rules, Thick
   rules, Check results, Proposed changes. Each finding: file, line, what, proposed action. Done when every finding from
   steps 2-8 appears once.
10. **Propose changes on a separate branch.** Branch `harness/checkup-<YYYY-MM-DD>` from the rendezvous commit, apply
    the mechanical fixes (stale names, dead pointers, duplicate → pointer), commit with scope `harness:`, and leave the
    branch local for a human to review and merge. Judgement calls (removing a rule, adding a check) stay as proposals in
    the report. Done when the branch exists and the synthesis branch is untouched.

## Rules

- Change nothing on the synthesis branch or any experiment branch; the checkup is reported separately so the synthesis
  PR stays about evidence.
- Propose, never loosen: a rule that constrains the agent is removed only by a human.
- The report stays local in `.local/drafts/`; it goes through outbound review before it is posted anywhere.

## Output

The final message names the report path, the branch name, and the counts per section.
