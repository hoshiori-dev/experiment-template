# The change brief

Load this when assembling the brief for the owner's confirmation. The brief is what the owner agrees to; it states
what changes and the facts the change rests on, never file lists or edit steps. Present it in the conversation, in
the conversation's language, complete each time.

## Shape

1. **Header**: what is being adapted (one line), what prompted it, and the status line "confirmed by <owner> on
   <absolute date>" once it is confirmed.
2. **Changes**: one entry per decision that changes.

   ```markdown
   - **<Decision>**: <current value> -> <new value>
     - Why: <the owner's reason, in one sentence>
     - Cost accepted: <what this option costs, from decisions.md or the discussion>
   ```

3. **Facts decided**: values only the owner could give and the change depends on (project name and objective,
   owner login, document language, where runs execute, tracker location, repository visibility). One line each.
4. **Unchanged**: every decision in scope that stays, with its current value, so silence is never read as "nobody
   checked". Decisions out of scope for a named change are listed in one line as not examined.
5. **Trade-offs settled**: each tension raised during the questions, the resolution, and the reason. State "none"
   when there were none.
6. **Owner's manual steps**: what only the owner can do, and whether it must happen before or after the merge
   (platform protection, token scopes, labels, visibility switch, history review).
7. **Untested after this change**: alternatives that will exist in the repository without a Formal Run having
   used them.
8. **Findings**: anything the probes showed that is inconsistent today, with the proposed correction; the owner
   confirms these with the rest.

## Rules

- Every entry carries the current value as read from the repository by its probe, not as remembered or as the
  template shipped it.
- One decision, one entry. A change that forces another (visibility forces the publishing standard) appears as
  two entries, the second naming the first as its reason.
- Nothing appears in Part 2 of the procedure that has no entry here.
