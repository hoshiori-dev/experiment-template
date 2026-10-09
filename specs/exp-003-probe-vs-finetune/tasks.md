# Tasks: exp-003-probe-vs-finetune

Rolling ledger. Tasks are numbered `T001`, `T002`, ... and a number is never reused. A task in state `planned` may be
edited or removed freely. A task in state `done` or `abandoned` stays in the ledger forever; `abandoned` carries its
reason. Finishing the Experiment does not require an empty ledger.

States: `planned`, `in progress`, `done`, `abandoned (reason)`.

| ID   | Task                                                                | State   | Notes                                                                                                |
| ---- | ------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------- |
| T001 | Fetch both inputs at their declared versions and verify them        | done    | both inputs fetched; markers under `.local/data/`                                                    |
| T002 | Write the training script and the environment definition            | done    | `train.py`, `make_design.py`, `Dockerfile`, own lock                                                 |
| T003 | Size the design with informal runs that skip test evaluation        | done    | two sizing runs, tuning split only; the first grid peaked at its top edge, so the grid moved up      |
| T004 | Commit the design file: manifest, tuning split, epochs, grid, seeds | done    | `design.json`: 80 fit, 20 tuning, 50 test images per class; 10 epochs; six learning rates; seeds 0-2 |
| T005 | Formal Run: both arms under the committed design                    | planned |                                                                                                      |
| T006 | Write the README from the Formal Run and close out                  | planned |                                                                                                      |
