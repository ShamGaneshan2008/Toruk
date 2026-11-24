"""Additional independent probabilities, overlap, gates, table and link checks."""

import hashlib
import json
import math
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job_v2 import verify_seal  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    audit = read(BASE / "independent-audit.json")
    summary = read(BASE / "registered/execution/summary.json")
    plan = read(BASE / "plan-final.json")
    draft = read(BASE / "plan.json")
    for key in draft:
        if key != "sources":
            assert draft[key] == plan[key], key
    for name, digest in draft["sources"].items():
        assert hashlib.sha256((BASE / "sources" / name).read_bytes()).hexdigest() == digest
    assert (
        summary["target_training_gain"]
        == sum(
            audit["cells"][f"{seed}-{model}-first16"]["training"]["metrics"]["exact"]
            - audit["cells"][f"{seed}-{model}-uniform"]["training"]["metrics"]["exact"]
            for seed in plan["crossed_seeds"]
            for model in ("ordinary", "recurrent")
        )
        == 0
    )
    assert summary["training_improvement"] is False
    assert read(BASE / "preservation-after.json")["all_unchanged"]
    train = read(BASE / "train-labels.json")
    assert summary["training_gate"]  # Only this passed gate permits dev inspection here.
    dev = read(BASE / "dev-labels.json")
    prior = read(ROOT / "artifacts/local-answer-dev-v1/train-labels.json")
    prior += read(ROOT / "artifacts/local-answer-dev-v1/dev-labels.json")
    prior += read(ROOT / "artifacts/local-answer-value-start-dev-v1/dev-labels.json")
    entity_values = lambda labels: {(r["canonical"][0], r["canonical"][2]) for r in labels}
    assert not entity_values(dev) & (entity_values(train) | entity_values(prior))
    report = ROOT / "docs/research/local-answer-value-start-replication-v2-results.md"
    text = report.read_text(encoding="utf-8")
    table = [line for line in text.splitlines() if re.match(r"\| (601|947) \|", line)]
    assert len(table) == 16
    for line in table:
        parts = [p.strip() for p in line.split("|")[1:-1]]
        init, shuffle, model, arm = parts[:4]
        cell = audit["cells"][f"i{init}-s{shuffle}-{model}-{arm}"]
        tr, de = cell["training"]["metrics"], cell["development"]["metrics"]
        cats = lambda m: "/".join(str(m["categories"][k]) for k in ("city", "code", "unknown"))
        flags = lambda m: f"{m['eos']}/{m['malformed']}/{m['repetition']}"
        assert parts[4:] == [
            str(tr["exact"]),
            cats(tr),
            flags(tr),
            str(de["exact"]),
            cats(de),
            flags(de),
            str(de["known_context_gain"]),
        ]
    probability_records = 0
    for stage in rows(BASE / "registered/execution/stages.jsonl"):
        if stage["stage"].startswith("fit-"):
            continue
        directory = BASE / "registered/execution" / stage["path"]
        vectors = rows(directory / "first-vectors.jsonl")
        metrics = rows(directory / "first-measurements.jsonl")
        for raw, metric in zip(vectors, metrics, strict=True):
            logits = raw["logits"]
            gold, pred = metric["expected_first_id"], metric["predicted_first_id"]
            mx = max(logits)
            z = sum(math.exp(v - mx) for v in logits)
            ze = sum(math.exp(logits[i] - logits[pred]) for i in range(2, 259))
            values = dict(
                expected_probability_full=math.exp(logits[gold] - mx) / z,
                predicted_probability_full=math.exp(logits[pred] - mx) / z,
                expected_probability_eligible=math.exp(logits[gold] - logits[pred]) / ze,
                predicted_probability_eligible=1 / ze,
            )
            assert all(
                math.isclose(metric[k], v, rel_tol=1e-12, abs_tol=1e-12) for k, v in values.items()
            )
            probability_records += 1
    assert probability_records == 1952
    scopes = [
        read(BASE / path / "cost.json")
        for path in (
            "preparation/budget",
            "registered/budget",
            "audit-execution",
            "verification/execution",
        )
    ]
    for path in ("audit-execution", "verification/execution"):
        verify_seal(BASE / path)
    assert all(
        c["status"] == "PASS" and c["complete_process_lifetimes"] and not c["active_processes"]
        for c in scopes
    )
    assert all(c["returncode"] == 0 for c in read(BASE / "verification/checks.json")["checks"])
    assert f"CPU{sum(c['cpu'] for c in scopes):.6f}" in text
    links = 0
    for path in (
        report,
        ROOT / "docs/research/local-answer-value-start-replication-v2-protocol.md",
    ):
        raw = path.read_bytes()
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
        assert all(line == line.rstrip() for line in raw.decode().splitlines())
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", raw.decode()):
            assert (path.parent / target).is_file(), target
            links += 1
    result = dict(
        status="PASS",
        accuracy_table_rows=16,
        probability_records=probability_records,
        development_entity_value_overlap=0,
        links=links,
        new_model_forwards=0,
        total_named_cpu=sum(c["cpu"] for c in scopes),
        total_named_wall=sum(c["wall"] for c in scopes),
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
