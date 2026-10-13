---
name: adapt-template
description: >
  Changes this research harness at the architecture level, with the owner deciding every point before any file is
  touched: first agrees what changes and which facts must be decided, then applies the change to every file that
  states it. Use when a repository was just created from the template; when the owner asks to set the project up,
  switch the governance model or external writes, make the repository private or public, move to another hosting
  platform, execution environment or tracker, change the branch structure, the dependency baseline, agent
  attribution, the commit address or the owner handle; when README.md still describes the template instead of the
  project; or when AGENTS.md "Current settings" must change. Works the same on a fresh copy and on a project that
  was adapted before. Not for starting an Experiment, writing a spec or an Epic, or the periodic harness check-up.
---

# Adapt the harness

Role: you carry out an architecture-level change of the harness for the owner. Goal: the owner has confirmed, in
the conversation, exactly what changes and every fact the change depends on; after that, every file that states a
changed value says the new one. Everything about adaptation lives in this skill directory and is read only while
this skill runs; other knowledge files state the project as it is, never the options.

## The consensus gate

Until the owner confirms the complete change brief presented in the conversation, change no file, create no branch
and write nothing outside the conversation. Questions, suggestions and every interim version of the brief live in
the dialogue. A file edited before consensus records a decision the owner has not made, and each such edit is one
more place where the harness disagrees with itself.

## The project as it is now

This skill never assumes the repository is still the template. The current value of every decision is read from
the repository each time, with the probe that [references/decisions.md](references/decisions.md) gives for it; the
reference files describe decisions, options and costs, and say nothing about which option this project uses. So:

- Never record this project's choices in this skill directory. Current values have their own homes (AGENTS.md
  "Current settings", `README.md`, the files the probes name).
- A reference file changes only to add or correct an option itself (for example notes for a backend nobody had
  described). Such an edit is an item of the brief and is made in Part 2, like every other edit.
- A probe that finds nothing, or two files that disagree about the current value, is a finding: put it in the
  brief as a fact to settle before anything else changes.

## Procedure

### Part 1: agree what changes

1. **Read the ground.** Read [references/decisions.md](references/decisions.md), AGENTS.md "Current settings" and
   `README.md`, and run the probes for the decisions in play (all of them on a first adaptation). Probes only read:
   no script or recipe that writes anywhere. Also read the state of the work: open Epics and experiment pull
   requests, experiment and run branches, run records and tracker data that exist. Harness changes belong to the
   preparation phase; with Experiments in flight, whether to proceed now and what happens to runs already recorded
   (their evidence stays where it was written; finished Experiments are not edited) is a question for the owner.
   Done when: you can state each decision's current value and where you read it, and whether work is in flight.

2. **Frame the change.** Establish with the owner what prompts it (a fresh copy to set up, or a named change to a
   working project), what the project is for, and who works in it. Every suggestion you make later is reasoned
   from these facts.
   Done when: you can say in two sentences what is being adapted and why.

3. **Interrogate in rounds.** Ask through the host's question tool (plain messages when the host has none), several questions per round, grouped by theme,
   only the decisions whose prerequisites are settled (the order is in decisions.md). For a named change, ask about
   that decision and every decision it opens (the "Opens" line of its entry in decisions.md), not the whole list. Attach a suggested answer wherever one can be
   inferred from the frame, the current value or the costs in decisions.md, and name the cost of each alternative.
   Ask bare what only the owner knows: project name and objective, the language of human-facing documents, the
   owner's platform login, where runs execute, which tracker, whether the repository is public. When two answers
   pull against each other (external writes on without platform protection; a private repository with the public
   publishing standard), put the tension to the owner as an explicit trade-off with a proposed resolution. When
   the answer points to another platform, execution environment or tracker, read
   [references/backends.md](references/backends.md) before the next round.
   Done when: every decision in scope has an answer or an explicit "keep as it is", and no open point remains.

4. **Present the complete change brief.** Read [references/change-brief.md](references/change-brief.md) and
   present the brief in the conversation in that shape: what changes (from, to), facts decided, what stays, costs
   accepted, what the owner does by hand. The brief says what and why; which files and how come in Part 2.
   Done when: the owner has said yes to the complete brief as presented. An answer given in a question round is
   not that confirmation; a correction means a revised complete brief and a new confirmation.

### Part 2: apply what was agreed

5. **Record the brief.** Write the confirmed brief to `.local/drafts/adaptation-brief.md`; it is the single source
   for the rest of the work and is not committed.

6. **Locate every statement.** For each change, list the files that state the old value: start from the "Stated
   in" entries of decisions.md, confirm each exists, then `git grep -n` the old value itself (the old login, the old governance word, the old tracker name) across
   every tracked file. For another execution environment, tracker or platform,
   add the scripts that talk to it and their tests, keeping the exit codes and outputs `scripts/README.md`
   documents.
   Done when: every grep hit is either on the list or explained as unrelated.

7. **Apply.** Edit the listed files only, and nothing the brief does not cover. On a first adaptation rewrite
   `README.md` as the project's own document (how the repository works shrinks to a short section pointing to
   AGENTS.md) and keep the mirror faithful. After editing anything under `speckit/`, run `just speckit-install`.
   An alternative built now and never used by a Formal Run is listed in the README's "Not implemented or untested"
   section until one has used it.
   Done when: the old values appear nowhere outside Git history.

8. **Verify.** Run `just check`, `just status`, `just outbound <every changed file>`, and the read-only platform checks whose scripts or settings changed
   (`just epic-status <n>`, `just spec-approval <exp-id>` against an existing issue or Experiment). Run the probes again: each returns the value in the brief. Then have a clean-context agent
   read only AGENTS.md and `.agents/knowledge/governance.md` and state the governance model, whether it may push,
   open issues, label and merge, and who merges protected paths; fix files until its answer matches the brief.
   Done when: all commands exit 0, the probes match, and the independent reading matches.

9. **Hand over.** Tell the owner the manual steps from the brief (platform settings are listed in
   `.agents/knowledge/tooling.md`), what is untested, and where the change sits. The change touches protected
   paths: commit it on a branch `adapt/<slug>` and stop; the owner merges it. In a copy that has no commit of the
   harness yet, leave the changes uncommitted and say so; the owner makes the first commit.

## Gotchas

- Something the brief does not cover turns up while applying (a file that states a value nobody asked about, an
  option that needs a further decision): stop, put it to the owner, present the amended complete brief, get it
  confirmed, update `.local/drafts/adaptation-brief.md`, then continue. Never settle it yourself.
- Switching external writes on without the platform protection in place leaves "protected paths are merged by
  humans" unenforced; the platform step comes before the permission-file change.
- A login left from the template in `.github/CODEOWNERS` grants harness review to an outsider; confirm with
  `git grep` that the old login appears nowhere else.
- A platform, tracker or address change can require a scanner or hook rule to change (for example the noreply
  domain of a self-managed platform in `.gitleaks.toml` and `scripts/check_commit_message.py`). That is an owner
  decision recorded in the brief, never an edit made to get a failing scan to pass.
- The owner may want a mix the two governance models do not define (for example "I approve every spec, the agent
  merges"). Name the nearest defined model, state what differs, and let the owner choose; a third model means
  rewriting `governance.md` first and is its own item in the brief.
- "Unlimited" budget and the budget unit are written in each Epic, not in a file; they are not adaptation
  decisions.
