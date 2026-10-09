# Outbound review

Read this before anything leaves this machine: a push, a pull request, an issue, a comment, an image push, a tracker
sync, or a file handed to a human to post. Source of truth for the public-repository publishing standard; the procedure
is the `outbound-review` skill, the five forbidden classes and the three rules are in `governance.md`.

## Why two passes

The repository is public. Pushed or posted content is public at once and stays in caches and forks after deletion, so
review happens before content leaves. A scanner knows patterns, not meaning; an agent reads meaning but misses patterns
it did not look for. Both passes must pass.

## What counts as outbound

| Outbound                                                       | Not outbound                               |
| -------------------------------------------------------------- | ------------------------------------------ |
| every commit about to be pushed (content, message, author)     | commits that stay local                    |
| Epic drafts, experiment issues, PR titles and bodies, comments | `.local/` contents, until copied elsewhere |
| result files copied into `experiments/<id>/` for the README    | run outputs under `.local/runs/`           |
| images pushed to a registry, tracker data synced to a remote   | local images, `.local/trackio/`            |
| drafts in `.local/drafts/` at the moment they are handed over  | notes that never leave the machine         |

Run records and manifests are outbound: they ship with the repository, which is why they hold only relative paths and
neutral aliases (`evidence.md`).

## Pass one: mechanical scan

- Files or directories: `just outbound <path>...` (`scripts/outbound_check.py`): runs gitleaks with `.gitleaks.toml`
  (default secret rules plus the extended rules for emails, public IPs and absolute home paths), found on PATH or in the
  pre-commit cache; with neither it exits 2 and names the fix (`pre-commit install --install-hooks`). Prints rule id and
  `file:line` only; exits non-zero on any finding.
- Working tree: `just scan` (the same script over every file git tracks or would add). Staged changes are scanned by the
  gitleaks pre-commit hook; outgoing commits by the pre-push hook (`scripts/outbound_check.py --git-range`). A hook
  failure is fixed at its cause.
- Drafts: write the text to `.local/drafts/<name>.md` and run `just outbound .local/drafts/<name>.md`.

## Pass two: read-through

Run the `outbound-review` skill over the same content. It looks for the five classes and for what the scanner cannot
see: a dataset path that names a person, a bucket or hostname spelled as prose, a quoted log line with an internal
address, a result file carrying raw data, a comment revealing unreleased material, confidential content the owner did
not clear.

## Reporting a finding

Name the class and the location (`file:line`, or the draft and paragraph). Never quote the value, and never paste it
into a tool call, a commit message or a conversation. Then rewrite the content and run both passes again.

## One hard guardrail

Content passes a scan by being rewritten, never by changing the scanner: no edit to `.gitleaks.toml`, no allowlist
entry, no `.gitleaksignore` line, no bypass flag (`--no-verify`, `SKIP=`, `--exit-code 0`). The positive steps (scope,
scan, read through, report, rewrite, hold) are the `outbound-review` skill's procedure.

## Posting

External writes on (current): every issue, PR body and comment is a draft in `.local/drafts/`, reviewed with both
passes, then posted by the agent from that file (`gh issue create`, `gh pr create`, `gh pr comment`, `gh issue comment`,
each with `--body-file`); the agent pushes its own branch after the pre-push hook passes.

External writes off: the reviewed draft is handed to a human who posts it. Pushing is the human's act too, and the
agent's branch stays local until then.

## After an accidental leak

Stop. Tell the human which class and where (commit, file, line, or issue and comment). Do not push a fix-up, amend,
force-push or delete to cover it: history rewriting and key rotation are the human's decisions, and the content is
already in caches. Resume only on the human's instruction.
