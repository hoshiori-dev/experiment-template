# Experiment starter

`template/experiment/` is a copyable starting point for one experiment, and `template/run-record.yaml` is an annotated
run record. The starter is one way to meet the boundaries of a formal run (committed code, frozen hashed dependencies,
declared data versions, declared resources); it is not a mandate. Replace any file with what the experiment needs, as
long as the boundaries still hold. Container and lock-file mechanics in it are the machine-learning example.

## Start an experiment

1. Have an experiment issue under a published Epic. Its number gives the ID `exp-NNN-<slug>` (NNN zero-padded to three
   digits, slug two to four lowercase words joined by `-`).
2. Copy the starter: `cp -r template/experiment experiments/<id>`. The spec, plan and tasks go to `specs/<id>/` (the
   Spec Kit research commands create them).
3. Rename: `name` in `experiments/<id>/pyproject.toml`, and the title line of `experiments/<id>/README.md`.
4. Keep `pyproject.toml` and `uv.lock` as copied: they are the project's dependency baseline, and Experiments with the
   same lock share one installed environment. When the baseline lacks what the Experiment needs, reuse the lock of an
   earlier Experiment that has it before resolving anything new; otherwise add the dependency and run `uv lock` here (it
   keeps the existing pins), and say in the plan why. After renaming the project run `uv lock`: it rewrites only the
   project's own entry, and the exported manifest stays byte-identical. The experiment is not a member of the root
   workspace; shared libraries are path dependencies (see the comment in `pyproject.toml`).
5. Commit on the branch named `<id>`; every path belongs under `specs/<id>/` or `experiments/<id>/`.

## What the files are

| File                 | Purpose                                                                                              |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| `README.md`          | The deliverable: six fixed sections and a status line. Must stand alone after `specs/<id>/` is gone. |
| `pyproject.toml`     | The experiment's dependency declaration; ships as the project baseline.                              |
| `uv.lock`            | The baseline lock. The experiment owns its copy; it stays identical unless the plan gives a reason.  |
| `Dockerfile`         | Example environment: hash-verified manifest in a layer of its own, source in a later layer.          |
| `.dockerignore`      | Keeps local environments and caches out of the build context.                                        |
| `../run-record.yaml` | Annotated run record; copy it to `experiments/<id>/runs/R001.yaml` and fill it in.                   |

`runs/` is created by the first formal run (record `R001.yaml` plus frozen manifest `R001.requirements.txt`); the
starter ships no `runs/` directory because an empty directory has nothing to say and a placeholder file would be
mistaken for a record. Other directories (source, configs, results, notebooks, tests) are created when there is content
for them.

## Formal run, in short

A run lives on branch `run/<id>/R###`, cut from the experiment branch. Its first commit (the source commit) adds the
record, the frozen manifest and run-specific inputs; nothing else is committed before the run starts. After the run,
append the outcome fields and the result files, then merge the run branch back with a merge commit. Freeze the manifest
from the experiment's lock, for example (without PyTorch):

```sh
uv export --format requirements.txt --locked --no-dev --no-emit-project --no-emit-local --no-header --no-annotate -o runs/R001.requirements.txt
```

`--no-header` and `--no-annotate` leave out the comments that repeat the command and the project name, so manifests of
the same dependencies are byte-identical across runs and Experiments; `--no-emit-local` drops path dependencies (they
carry no hash); build shared libraries as wheels with `uv build --package <lib>` from the root and install them
separately. With PyTorch, the manifest is compiled for one exact accelerator backend and the image installs with the
same `--torch-backend=cuXXX`; the two commands are in `.agents/knowledge/evidence.md` (Environment).
`just preflight <id> R001` checks the start conditions that a machine can check.
