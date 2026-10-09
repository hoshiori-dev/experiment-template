# Tasks: exp-003-probe-vs-finetune

Rolling ledger. Tasks are numbered `T001`, `T002`, ... and a number is never reused. A task in state `planned` may be
edited or removed freely. A task in state `done` or `abandoned` stays in the ledger forever; `abandoned` carries its
reason. Finishing the Experiment does not require an empty ledger.

States: `planned`, `in progress`, `done`, `abandoned (reason)`.

| ID   | Task                                                                | State   | Notes |
| ---- | ------------------------------------------------------------------- | ------- | ----- |
| T001 | Fetch both inputs at their declared versions and verify them        | planned |       |
| T002 | Write the training script and the environment definition            | planned |       |
| T003 | Size the design with informal runs that skip test evaluation        | planned |       |
| T004 | Commit the design file: manifest, tuning split, epochs, grid, seeds | planned |       |
| T005 | Formal Run: both arms under the committed design                    | planned |       |
| T006 | Write the README from the Formal Run and close out                  | planned |       |
