"""Read-only comparison of the results document with saved numerical evidence."""

import json
import math
import re
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
REPORT = ROOT / "docs/research/answer-trainability-dev-v1-results.md"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def close(actual, expected, tolerance=0.00000051):
    assert math.isclose(float(actual), expected, rel_tol=0, abs_tol=tolerance), (actual, expected)


def table(text, start, end):
    section = text.split(start, 1)[1].split(end, 1)[0]
    lines = [line for line in section.splitlines() if line.startswith(("| 419 |", "| 733 |"))]
    assert len(lines) == 8
    return [[part.strip() for part in line.split("|")[1:-1]] for line in lines]


def main():
    text = REPORT.read_text(encoding="utf-8")
    analysis = read(RUN / "diagnostic-summary.json")
    summary = read(RUN / "summary.json")
    for parts in table(text, "| Seed | Objective | Model | Train exact/EOS", "All training outputs"):
        seed, objective, variant = parts[:3]
        cell = analysis["cells"][f"{seed}-{objective}-{variant}"]
        train = cell["evaluations"]["train"]["metrics"]
        dev = cell["evaluations"]["dev"]["metrics"]
        assert parts[3] == f'{train["exact"]}/{train["eos"]}'
        assert list(map(int, parts[4:8])) == [dev[k] for k in ("exact", "eos", "malformed", "repetitive")]
        assert parts[8] == f'{dev["categories"]["city"]}/8,{dev["categories"]["code"]}/4,{dev["categories"]["unknown"]}/4'
    for parts in table(text, "| Seed | Objective | Model | Train full NLL", "The unique training file"):
        seed, objective, variant = parts[:3]
        cell = analysis["cells"][f"{seed}-{objective}-{variant}"]
        train = cell["evaluations"]["train"]["metrics"]
        dev = cell["evaluations"]["dev"]["metrics"]
        for actual, expected in zip(parts[3:], (train["full_nll"], train["answer_nll"], dev["full_nll"], dev["answer_nll"]), strict=True):
            close(actual, expected)
    for parts in table(text, "| Seed | Objective | Model | Answer share", "Loss shares sum"):
        seed, objective, variant = parts[:3]
        stats = analysis["cells"][f"{seed}-{objective}-{variant}"]["contributions"]
        close(parts[3].removesuffix("%"), stats["summed_weighted_answer_loss_fraction"]*100, 0.000051)
        for actual, key in zip(parts[4:], ("mean_history_parameter_gradient_l2", "mean_answer_parameter_gradient_l2", "mean_answer_projection"), strict=True):
            close(actual, stats[key])
    for parts in table(text, "| Seed | Objective | Model | Cold fit CPU/wall", "Per-cell cold training"):
        seed, objective, variant = parts[:3]
        cell = analysis["cells"][f"{seed}-{objective}-{variant}"]
        for actual, values in ((parts[3], cell["cold_training"]), (parts[4], cell["training"]["loop"]), (parts[6], cell["evaluations"]["dev"]["cold_generation"]), (parts[7], cell["evaluations"]["dev"]["cold_scoring"])):
            for number, key in zip(actual.split("/"), ("cpu", "wall"), strict=True):
                close(number, values[key])
        assert int(parts[5]) == cell["cold_training"]["peak_private"]
    examples = [
        ("train-000, all8 cells", "train", 0, list(analysis["cells"])),
        ("dev-000, all8 cells", "dev", 0, list(analysis["cells"])),
        ("dev-006,419 answer16 ordinary", "dev", 6, ["419-answer16-ordinary"]),
        ("dev-008,419 answer16 ordinary", "dev", 8, ["419-answer16-ordinary"]),
        ("dev-011,419 uniform recurrent", "dev", 11, ["419-uniform-recurrent"]),
        ("dev-012,733 uniform recurrent", "dev", 12, ["733-uniform-recurrent"]),
    ]
    for caption, split, index, names in examples:
        line = next(s for s in text.splitlines() if s.startswith("| " + caption + " |"))
        parts = [s.strip() for s in line.split("|")[1:-1]]
        ids = json.loads(re.search(r"`(\[[0-9,]+\])`", line).group(1))
        for name in names:
            path = RUN / "stages" / f"generate-{split}-{name}" / "predictions.jsonl"
            prediction = json.loads(path.read_text().splitlines()[index])
            assert prediction["result"]["generated_ids"] == ids
            assert prediction["prefix"][31:] == parts[1].strip("`").replace("\\n", "\n")
    links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
    assert all((REPORT.parent / link).is_file() for link in links)
    total = {key: sum(v[key] for k, v in summary["metrics"].items() if k.startswith("dev-")) for key in ("exact", "eos", "malformed", "repetitive")}
    assert total == dict(exact=49, eos=121, malformed=11, repetitive=0)
    for name in (REPORT, ROOT / "docs/research/answer-trainability-dev-v1-protocol.md", ROOT / "scripts/answer_trainability_dev.py", ROOT / "tests/test_answer_trainability_dev.py"):
        raw = name.read_bytes()
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
        assert all(line == line.rstrip() for line in raw.decode().splitlines())
    print(json.dumps(dict(status="PASS", numerical_table_rows=32, representative_rows=6,
                         example_predictions_checked=20, links=len(links), development=total)))


if __name__ == "__main__":
    main()
