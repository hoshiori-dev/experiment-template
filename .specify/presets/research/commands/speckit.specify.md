---
description: Start an Experiment from an experiment issue - branch, spec, README, draft pull request.
argument-hint: "Experiment issue number, e.g. 23"
---

## User Input

```text
$ARGUMENTS
```

## Role and goal

You open one Experiment for one experiment issue. Done means: the branch `<id>` exists with `specs/<id>/spec.md`,
`specs/<id>/plan.md`, `specs/<id>/tasks.md` and `experiments/<id>/README.md` committed, and the pull request body is
ready for the human. Read `.agents/knowledge/governance.md` first: it holds the governance model, the two gates and the
stopping rules this command enforces.

## Steps

1. **Issue number.** `$ARGUMENTS` holds the experiment issue number, an integer. Without one, stop and ask for it; an
   Experiment starts only from an existing experiment issue in the main repository. Done when: `N` is known.

2. **Read the issue (read-only).** Run `gh issue view N --json parent,title,body,labels`. Require the label `experiment`
   and a non-null `parent`. Stop and tell the human when either is missing: a missing parent means the issue is not
   attached to an Epic, and an Experiment needs one. Done when: `P` (the parent issue number), the title and the body
   are in hand.

3. **Epic validity.** Run `just epic-status P`. Exit 0 continues. Exit 1 prints the reasons: stop and report them. Exit
   2 means the platform was unreachable after retries: stop and say so; an Epic is never assumed valid. Done when:
   `just epic-status P` exited 0.

4. **Derive the ID.** `id = exp-NNN-<slug>`: `NNN` is `N` zero-padded to three digits; the slug is two to four lowercase
   words from the issue title, joined by `-`. The short form `exp-NNN` is the scope of every commit on this branch.
   Check `git branch --all --list '*exp-NNN-*'` and `specs/`: when the number already has an Experiment, stop and point
   to it. Done when: the ID is unique.

5. **Branch and directories.** From a clean working tree: `git switch -c <id> main`,
   `mkdir -p specs/<id>
   experiments/<id>`, and write `.specify/feature.json` with content
   `{"feature_directory": "specs/<id>"}`. Done when: `git branch --show-current` prints `<id>`.

6. **Spec, plan, tasks.** Resolve each template with `.specify/scripts/bash/resolve-template.sh <name>` for
   `spec-template`, `plan-template`, `tasks-template` (it returns the preset's replacement); when the script fails, copy
   `.specify/presets/research/templates/<name>.md` instead, the same content. Write them to `specs/<id>/spec.md`,
   `plan.md`, `tasks.md`. Fill the spec from the issue body and the Epic text: front matter `experiment`, `issue`,
   `budget` (unit from the Epic, `limit` at most the allotment written on the issue; omit the block when the Epic says
   "unlimited"), `holdout`, and every section. Where the issue leaves a constraint open, write the question into the
   section as `OPEN: ...` so the reviewer resolves it before approval; invent nothing, and never a budget number. Done
   when: every template heading is present and no `exp-NNN-slug` placeholder remains.

7. **Experiment README.** Copy `template/experiment/README.md` to `experiments/<id>/README.md`, set the title to `<id>`
   and the status line to `in progress`, fill `Question` from the spec and leave the other sections with their template
   text. Done when: the README names the question and the six fixed sections exist.

8. **Commit.** `git add specs/<id> experiments/<id>` and commit with the title `exp-NNN: open experiment`. The
   commit-msg hook rejects attribution trailers and non-noreply author addresses; fix the cause when it fails, never
   bypass the hook. Done when: `git log --oneline -1` shows the commit on branch `<id>`.

9. **Pull request draft, then stop.** Read `.agents/knowledge/publishing.md` before writing anything that leaves the
   machine. Write the PR body to `.local/drafts/<id>-pr.md`, following `.github/PULL_REQUEST_TEMPLATE.md` when it
   exists: the issue reference `#N`, the Epic `#P`, the question, the budget, and the request to review the spec. Run
   `just outbound .local/drafts/<id>-pr.md`; on findings rewrite the draft and run it again. Done when: the draft passes
   `just outbound`.

## Hand-over

- **High-automation mode with external writes on** (the shipped default; AGENTS.md "Current settings" states the current
  value): push the branch, open the PR with `gh pr create --title "<id>" --body-file .local/drafts/<id>-pr.md`, then
  request approval through `/speckit-research-approve <id>` executed by a fresh sub-agent that holds none of this
  conversation's context. Nothing runs as evidence before the label `spec:approved` exists.
- **External writes off**: stop here. Tell the human: push branch `<id>`, open the pull request with the draft body,
  review the spec, and apply the label `spec:approved` when they accept it.

Next acts: the human (or the approving agent). Continue with `/speckit-implement` only after approval.
