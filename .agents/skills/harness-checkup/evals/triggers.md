# Trigger cases

Each prompt goes, unchanged, to a fresh clean-context agent that is not told which skill is under test; method in
`.agents/knowledge/tooling.md` (Skills). "Load" means this skill should be among the skills the agent loaded.

| #  | Prompt                                                                                                             | Expected    |
| -- | ------------------------------------------------------------------------------------------------------------------ | ----------- |
| H1 | Audit the harness for drift: stale paths, dead recipes, rules stated twice.                                        | load        |
| H2 | We are at the rendezvous for Epic 1 and about to synthesize. Do the periodic harness check first.                  | load        |
| H3 | Before we synthesize, check whether AGENTS.md and the knowledge files still point at paths and recipes that exist. | load        |
| H4 | The commit-msg hook rejects my commit title. Why?                                                                  | do not load |
| H5 | Change the harness so that external writes are off.                                                                | do not load |
| H6 | Check the budget of exp-003.                                                                                       | do not load |
