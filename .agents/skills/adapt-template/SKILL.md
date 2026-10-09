---
name: adapt-template
description: >
  Adapts this research template into one owner's project, or changes a factory setting later, changing every file
  that states the setting. Use when a repository was just created from the template; when the owner asks to set the
  template up for a project, switch the governance model or external writes, make the repository private, move to
  another hosting platform, execution environment or tracker, allow agent attribution, or change the owner handle;
  when README.md still describes the template instead of the project; or when AGENTS.md "Current settings" must
  change. Not for starting an Experiment, writing a spec or an Epic, or the periodic harness check-up.
---

# Adapt the template

Every setting change lands in every file that states it, with the owner deciding each point and nothing assumed.

## Procedure

1. **Read the ground.** Read `.agents/knowledge/adaptation.md` (the decision list, shipped values, alternatives, and
   which files each switch touches), AGENTS.md "Current settings", and `README.md`. State in one sentence whether this
   is the first adaptation of a fresh copy or a later change of named settings.
   Done when: you can list every decision adaptation.md names and its current value in this repository.

2. **Interrogate in rounds.** Ask the owner through the host's question tool, several questions per round, only the
   decisions whose prerequisites are settled; a decision that depends on an open one waits for the next round. Lead
   every question with the shipped value as the recommended option and name the cost of each alternative from
   adaptation.md. Ask bare, without a recommendation, what only the owner knows: project name and objective, the
   language of human-facing documents, the owner's platform login, the hosting platform, where runs execute, which
   tracker, whether the repository is public. First round: identity, platform, visibility, governance model. Second
   round: external writes (only meaningful once governance and platform are known), attribution, commit address,
   execution environment, tracker. Last round: anything the earlier answers opened.
   Done when: every decision in adaptation.md has an answer or the owner has said "keep the shipped value".

3. **Plan, then validate the plan.** Write `.local/drafts/adaptation-plan.md`: one section per decision with the
   chosen value and the exact files to change. Take the file list from adaptation.md; add `README.md`, the Chinese
   mirror `README.zh.md` (or the mirror in the chosen language), `.specify/memory/constitution.md`, and
   `.github/CODEOWNERS` for identity. For an execution environment, tracker, or platform other than the shipped one,
   add the scripts that talk to it (`scripts/tracker_lookup.py`; `scripts/epic_status.py` and
   `scripts/spec_approval.py` through `scripts/_gh.py`) and their tests, keeping the exit codes and the outputs that
   `scripts/README.md` documents, and mark the alternative as untested in adaptation.md until a run has used it.
   Check that every listed file exists and that no file stating a changed value is missing: `grep -rn` the old value
   (the old owner login, the old governance word, "external writes", the old tracker name) across AGENTS.md,
   README*.md, `.agents/`, `speckit/`, `.github/`, `scripts/`, `template/`, the three permission files.
   Show the plan to the owner and wait for approval.
   Done when: the owner approved the plan and every grep hit is in the plan.

4. **Apply.** Edit the planned files only. Rewrite README.md as the project's own document (the template's design
   summary moves to a short "how this repository works" section pointing to AGENTS.md), and keep the mirror
   faithful. After editing anything under `speckit/`, run `just speckit-install`. Record what was switched in
   adaptation.md's "Shipped value" column so the table describes this project, and record alternatives you built
   as untested until a Formal Run has used them.
   Done when: the old values no longer appear outside adaptation.md's alternatives column and git history.

5. **Verify.** Run `just check`, `just status`, `just outbound <every changed file>`, and the platform read-only
   checks that apply (`just epic-status <n>` against a test issue if one exists). Then have a clean-context agent
   read only AGENTS.md and `.agents/knowledge/governance.md` and state the governance model, whether it may push,
   open issues, label, and merge, and who merges protected paths; fix any file until its answer matches the owner's
   decisions.
   Done when: all commands exit 0 and the independent reading matches.

6. **Hand over.** List the platform settings the owner configures by hand (from `.agents/knowledge/tooling.md`:
   branch protection, code-owner review, token scopes, labels), the alternatives marked untested, and where the
   change sits. The adaptation changes protected paths: commit it on a branch `adapt/<slug>` and stop; the owner
   merges it. In a copy that has no commit of the harness yet, leave the changes uncommitted and say so; the
   owner makes the first commit.

## Gotchas

- "Unlimited" budget is written in each Epic, not in a file; it is not an adaptation decision.
- The five forbidden content classes, both human gates, and English for agent-facing files do not change; the owner
  can change the language of human-facing documents only (adaptation.md "What does not change").
- Switching external writes on without the platform protection in place leaves "protected paths are merged by
  humans" unenforced; put the platform step before the permission-file change in the plan.
- The owner login appears in `.github/CODEOWNERS` only; a login left from the template grants harness review to an
  outsider.
- A platform, tracker or address change can require a scanner or hook rule to change (for example the noreply
  domain of a self-managed platform in `.gitleaks.toml` and `scripts/check_commit_message.py`). That is an owner
  decision recorded in the plan, never an edit made to get a failing scan to pass.
- The owner may want a mix the two governance models do not define (for example "I approve every spec, the agent
  merges"). Name the nearest defined model, state what differs, and let the owner choose; a third model means
  rewriting `governance.md` first and is planned as its own decision.
