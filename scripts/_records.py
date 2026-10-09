"""Run records and spec front matter: paths, parsing, schema validation, budget arithmetic.

Schemas are the ones in the harness knowledge (``experiments/<id>/runs/R###.yaml`` and the
front matter of ``specs/<id>/spec.md``). Validation returns findings as strings; an empty
list means the record is valid.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from _git import branches, git, is_ancestor, rev_parse, show_file

EXP_ID_RE = re.compile(r"^exp-\d{3}-[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
RUN_ID_RE = re.compile(r"^R\d{3}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ISO_DURATION_RE = re.compile(
    r"^P(?!$)(?:\d+Y)?(?:\d+M)?(?:\d+W)?(?:\d+D)?"
    r"(?:T(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?)?$"
)
DATE_LIKE_RE = re.compile(r"^\d{4}-?\d{2}-?\d{2}(?:[T ].*)?$")
BRANCH_LIKE_VERSIONS = {
    "latest",
    "main",
    "master",
    "head",
    "develop",
    "dev",
    "trunk",
    "nightly",
    "stable",
    "current",
}
MACHINE_SPECIFIC_RE = re.compile(r"(/home/|/Users/|[A-Za-z]:\\|\b[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\b)")

PARAMS_SOURCES = {"git", "tracker", "mixed"}
ACCELERATORS = {"cpu", "gpu"}
OUTCOMES = {"completed", "failed", "aborted"}

DEFINITION_FIELDS = {
    "id",
    "experiment",
    "decision",
    "command",
    "params_source",
    "params_path",
    "data",
    "resources",
    "max_duration",
    "environment",
    "budget",
    "spec_digest",
    "tracker",
}
EXECUTION_FIELDS = {
    "outcome",
    "execution_ref",
    "failure_reason",
    "actual_usage",
    "interruptions",
}


def record_path(exp_id: str, run_id: str) -> str:
    return f"experiments/{exp_id}/runs/{run_id}.yaml"


def spec_path(exp_id: str) -> str:
    return f"specs/{exp_id}/spec.md"


def run_branch(exp_id: str, run_id: str) -> str:
    return f"run/{exp_id}/{run_id}"


def sha256_digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_front_matter(text: str) -> dict:
    """YAML front matter of a Markdown file as a dict; empty when the file has none."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    data = yaml.safe_load(text[3:end])
    return data if isinstance(data, dict) else {}


def parse_record(text: str) -> dict | None:
    """YAML run record as a dict; None when the text is not a mapping."""
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else None


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def nonempty(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _is_relative_path(value) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:", value):
        return False
    return ".." not in Path(value).parts


def _machine_specific_strings(value, where: str) -> list[str]:
    """Findings for strings that name a home directory, drive, user or host."""
    found = []
    if isinstance(value, str):
        if MACHINE_SPECIFIC_RE.search(value):
            found.append(f"{where}: names a home directory, drive, user or host")
    elif isinstance(value, dict):
        for key, item in value.items():
            found += _machine_specific_strings(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found += _machine_specific_strings(item, f"{where}[{index}]")
    return found


def version_is_immutable(value) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    lowered = value.strip().lower()
    if lowered in BRANCH_LIKE_VERSIONS or DATE_LIKE_RE.match(lowered):
        return False
    return "/" not in lowered


def validate_record(data: dict, label: str = "record") -> list[str]:
    """Schema findings for one run record; ``label`` prefixes each finding."""
    f: list[str] = []

    def need(key, check, what):
        if key not in data:
            f.append(f"{label}: {key} is missing")
        elif not check(data[key]):
            f.append(f"{label}: {key} {what}")

    need("id", lambda v: isinstance(v, str) and RUN_ID_RE.match(v), "must look like R001")
    need(
        "experiment",
        lambda v: isinstance(v, str) and EXP_ID_RE.match(v),
        "must look like exp-023-two-to-four-words",
    )
    need("decision", nonempty, "must be one sentence")
    need("command", nonempty, "must be the command that was run")
    need(
        "params_source",
        lambda v: v in PARAMS_SOURCES,
        "must be one of git, tracker, mixed",
    )
    if data.get("params_source") in {"git", "mixed"}:
        need(
            "params_path",
            _is_relative_path,
            "must be a relative repo path when params_source is git or mixed",
        )

    need("data", lambda v: isinstance(v, list), "must be a list of inputs")
    for index, entry in enumerate(data.get("data") or []):
        where = f"{label}: data[{index}]"
        if not isinstance(entry, dict):
            f.append(f"{where} must be a mapping with name, source, version, path")
            continue
        for key in ("name", "source"):
            if not nonempty(entry.get(key)):
                f.append(f"{where}.{key} is missing")
        if not version_is_immutable(entry.get("version")):
            f.append(f"{where}.version must be an immutable content identifier (never latest, a date or a branch name)")
        if not _is_relative_path(entry.get("path")):
            f.append(f"{where}.path must be a relative repo path")

    resources = data.get("resources")
    if not isinstance(resources, dict):
        f.append(f"{label}: resources must be a mapping with accelerator and count")
    else:
        if resources.get("accelerator") not in ACCELERATORS:
            f.append(f"{label}: resources.accelerator must be cpu or gpu")
        count = resources.get("count")
        if not (isinstance(count, int) and not isinstance(count, bool) and count >= 1):
            f.append(f"{label}: resources.count must be a positive integer")

    need(
        "max_duration",
        lambda v: isinstance(v, str) and ISO_DURATION_RE.match(v),
        "must be an ISO-8601 duration such as PT2H",
    )

    environment = data.get("environment")
    if not isinstance(environment, dict) or not environment:
        f.append(
            f"{label}: environment must map each frozen environment file "
            "(dockerfile, lockfile, requirements, ...) to a relative repo path"
        )
    else:
        for key, value in environment.items():
            if not _is_relative_path(value):
                f.append(f"{label}: environment.{key} must be a relative repo path")

    if "budget" in data:
        budget = data["budget"]
        if not (isinstance(budget, dict) and _is_number(budget.get("reserved")) and budget["reserved"] >= 0):
            f.append(f"{label}: budget.reserved must be a non-negative number")

    need(
        "spec_digest",
        lambda v: isinstance(v, str) and DIGEST_RE.match(v),
        "must be sha256:<64 hex digits> of specs/<id>/spec.md at the source commit",
    )

    tracker = data.get("tracker")
    if not isinstance(tracker, dict):
        f.append(f"{label}: tracker must be a mapping with project and run")
    else:
        for key in ("project", "run"):
            if not nonempty(tracker.get(key)):
                f.append(f"{label}: tracker.{key} is missing")

    if "outcome" in data:
        if data["outcome"] not in OUTCOMES:
            f.append(f"{label}: outcome must be completed, failed or aborted")
        if not _is_number(data.get("actual_usage")) or data["actual_usage"] < 0:
            f.append(f"{label}: actual_usage must be a non-negative number once an outcome is set")
        if data["outcome"] in {"failed", "aborted"} and not nonempty(data.get("failure_reason")):
            f.append(f"{label}: failure_reason must say why the run {data['outcome']}")
    elif "actual_usage" in data:
        f.append(f"{label}: actual_usage is set but outcome is missing")
    if "execution_ref" in data and not isinstance(data["execution_ref"], str):
        f.append(f"{label}: execution_ref must be a string")
    if "interruptions" in data:
        value = data["interruptions"]
        if not (isinstance(value, int) and not isinstance(value, bool) and value >= 0):
            f.append(f"{label}: interruptions must be a non-negative integer")

    for key in sorted(set(data) - DEFINITION_FIELDS - EXECUTION_FIELDS):
        f.append(f"{label}: {key} is not a record field; remove it")

    f += _machine_specific_strings(data, label)
    return f


def validate_record_location(data: dict, path: str, label: str) -> list[str]:
    """Findings when the record's id/experiment disagree with its path under experiments/."""
    f = []
    match = re.match(r"^experiments/([^/]+)/runs/([^/]+)\.yaml$", path.replace("\\", "/"))
    if not match:
        return f
    exp_id, run_id = match.groups()
    if data.get("experiment") != exp_id:
        f.append(f"{label}: experiment must be {exp_id} to match the record's directory")
    if data.get("id") != run_id:
        f.append(f"{label}: id must be {run_id} to match the file name")
    return f


@dataclass
class RunView:
    """One run record as the budget sees it: where it came from and what it costs."""

    run_id: str
    origin: str  # the ref the record was read from: base ref, run branch or extra ref
    data: dict | None
    findings: list[str] = field(default_factory=list)

    @property
    def outcome(self) -> str | None:
        return self.data.get("outcome") if self.data else None

    @property
    def reserved(self):
        budget = (self.data or {}).get("budget")
        return budget.get("reserved") if isinstance(budget, dict) else None

    @property
    def actual_usage(self):
        return (self.data or {}).get("actual_usage")


def unmerged_run_branches(repo: Path, exp_id: str, base: str) -> list[str]:
    """Run branches of ``exp_id`` whose tip is not reachable from ``base``."""
    found = []
    for name in branches(repo, f"run/{exp_id}/"):
        tip = rev_parse(repo, name)
        if tip and not is_ancestor(repo, tip, base):
            found.append(name)
    return found


def budget_base(repo: Path, exp_id: str) -> str:
    """Ref the budget is computed over: the experiment branch tip when it exists, else HEAD."""
    return exp_id if rev_parse(repo, exp_id) else "HEAD"


def records_at(repo: Path, exp_id: str, ref: str) -> list[str]:
    """Run ids whose record file exists in the tree of ``ref``."""
    out = git(["ls-tree", "--name-only", ref, f"experiments/{exp_id}/runs/"], repo, check=False)
    names = [Path(line).stem for line in out.splitlines() if line.endswith(".yaml")]
    return sorted(name for name in names if RUN_ID_RE.match(name))


def _view_from_ref(exp_id: str, run_id: str, ref: str, text: str | None) -> RunView:
    path = record_path(exp_id, run_id)
    label = f"{ref}:{path}"
    if text is None:
        return RunView(run_id, ref, None, [f"{label}: record is missing"])
    try:
        data = parse_record(text)
    except yaml.YAMLError as error:
        return RunView(run_id, ref, None, [f"{label}: {error}"])
    return RunView(run_id, ref, data, [] if data else [f"{label}: must be a YAML mapping"])


def collect_runs(repo: Path, exp_id: str, base: str = "HEAD", extra_refs: tuple[str, ...] = ()) -> list[RunView]:
    """Records in the tree of ``base``, plus records on every ``run/<exp-id>/*`` branch and in
    ``extra_refs`` that ``base`` does not contain.

    A later source wins for the same run: a copy on an unmerged run branch carries the later
    state of that run. Merged branches add nothing, ``base`` already holds their records.
    """
    views: dict[str, RunView] = {}
    for run_id in records_at(repo, exp_id, base):
        views[run_id] = _view_from_ref(exp_id, run_id, base, show_file(repo, base, record_path(exp_id, run_id)))
    for ref in extra_refs:
        tip = rev_parse(repo, ref)
        if not tip or is_ancestor(repo, tip, base):
            continue
        for run_id in records_at(repo, exp_id, ref):
            views[run_id] = _view_from_ref(exp_id, run_id, ref, show_file(repo, ref, record_path(exp_id, run_id)))
    for branch in unmerged_run_branches(repo, exp_id, base):
        run_id = branch.rsplit("/", 1)[1]
        views[run_id] = _view_from_ref(exp_id, run_id, branch, show_file(repo, branch, record_path(exp_id, run_id)))
    return [views[key] for key in sorted(views)]


@dataclass
class BudgetReport:
    exp_id: str
    unit: str | None
    limit: float | None  # None means the spec has no budget block (unlimited)
    spent: float
    reserve: float
    runs: list[RunView]
    findings: list[str]

    @property
    def fits(self) -> bool:
        return self.limit is None or self.spent + self.reserve <= self.limit

    def to_dict(self) -> dict:
        return {
            "experiment": self.exp_id,
            "unit": self.unit,
            "limit": self.limit,
            "spent": self.spent,
            "reserve": self.reserve,
            "fits": self.fits,
            "runs": [
                {
                    "id": run.run_id,
                    "origin": run.origin,
                    "outcome": run.outcome,
                    "reserved": run.reserved,
                    "actual_usage": run.actual_usage,
                }
                for run in self.runs
            ],
            "findings": self.findings,
        }


def load_spec_front_matter(repo: Path, exp_id: str) -> dict | None:
    """Front matter of the experiment's spec from the working tree; None when absent."""
    file = repo / spec_path(exp_id)
    if not file.is_file():
        return None
    return parse_front_matter(file.read_text(encoding="utf-8"))


def compute_budget(
    repo: Path, exp_id: str, reserve: float = 0.0, base: str | None = None, extra_refs: tuple[str, ...] = ()
) -> BudgetReport:
    """spent = actual_usage of finished runs + reserved of unfinished runs, all branches included.

    ``base`` defaults to ``budget_base``: the experiment branch tip when it exists, else HEAD.
    """
    findings: list[str] = []
    front = load_spec_front_matter(repo, exp_id)
    unit = limit = None
    if front is None:
        findings.append(f"{spec_path(exp_id)}: spec is missing")
    else:
        budget = front.get("budget")
        if budget is not None:
            if not isinstance(budget, dict) or not _is_number(budget.get("limit")):
                findings.append(f"{spec_path(exp_id)}: budget.limit must be a number")
            else:
                limit = float(budget["limit"])
                unit = budget.get("unit")
                if not isinstance(unit, str) or not unit:
                    findings.append(f"{spec_path(exp_id)}: budget.unit is missing")

    runs = collect_runs(repo, exp_id, base or budget_base(repo, exp_id), extra_refs)
    spent = 0.0
    for run in runs:
        findings += run.findings
        if run.data is None:
            continue
        label = f"{run.origin}:{record_path(exp_id, run.run_id)}"
        if run.outcome is not None:
            if _is_number(run.actual_usage):
                spent += float(run.actual_usage)
            else:
                findings.append(f"{label}: actual_usage must be a number once an outcome is set")
        elif _is_number(run.reserved):
            spent += float(run.reserved)
        elif limit is not None:
            findings.append(f"{label}: budget.reserved is missing but the spec sets a budget limit")
    return BudgetReport(exp_id, unit, limit, spent, float(reserve), runs, findings)
