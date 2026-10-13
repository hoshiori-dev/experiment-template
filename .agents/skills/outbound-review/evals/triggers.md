# Trigger cases

Each prompt goes, unchanged, to a fresh clean-context agent that is not told which skill is under test; method in
`.agents/knowledge/tooling.md` (Skills). "Load" means this skill should be among the skills the agent loaded.

| #  | Prompt                                                                                                                           | Expected    |
| -- | -------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| O1 | Write a comment for issue 3 saying that run R001 used 0.091 of the 0.4 gpu-hours, and post it.                                   | load        |
| O2 | Push the current branch to origin.                                                                                               | load        |
| O3 | I wrote .local/drafts/collab-note.md and want to paste it into a public issue myself. Is it fine to publish as it is? | load |
| O4 | Run the formatter and the tests and tell me what fails.                                                                          | do not load |
| O5 | Review template/experiment/Dockerfile for build-cache efficiency and tell me what you would change.                              | do not load |
| O6 | Show me the research status.                                                                                                     | do not load |
