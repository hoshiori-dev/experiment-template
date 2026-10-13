# Trigger cases

Each prompt goes, unchanged, to a fresh clean-context agent that is not told which skill is under test; method in
`.agents/knowledge/tooling.md` (Skills). "Load" means this skill should be among the skills the agent loaded.

| #  | Prompt                                                                                                                              | Expected    |
| -- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| A1 | I just created this repository from the template. Set it up for my project on protein stability prediction.                         | load        |
| A2 | From now on a human should approve every spec and merge every experiment pull request; the agent should stop doing that itself.     | load        |
| A3 | Our runs will go to a Slurm cluster instead of local Docker, and we want Weights & Biases for tracking. Make the repository say so. | load        |
| A4 | Change the harness so that external writes are off.                                                                                 | load        |
| A5 | Start the experiment for issue 12.                                                                                                  | do not load |
| A6 | The tracker lookup recipe exits with code 2 for run R001 of exp-003. Find out why.                                                  | do not load |
| A7 | Before we synthesize, check whether AGENTS.md and the knowledge files still point at paths and recipes that exist.                  | do not load |
