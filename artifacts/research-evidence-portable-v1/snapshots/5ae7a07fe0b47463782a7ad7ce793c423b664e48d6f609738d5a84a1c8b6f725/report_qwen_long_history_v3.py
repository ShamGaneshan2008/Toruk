"""Offline development-only v3 audit and report; never calls model generation."""

import argparse
import hashlib
import importlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path):
    return json.loads(path.read_bytes())


def sha(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path: Path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")


def rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    reg = read(run / "registration.json")
    for name, digest in reg["bindings"].items():
        assert sha(Path(name)) == digest, name
    source = Path(reg["config"]["source_checkout"])
    previous = ROOT / reg["config"]["v2_run"]
    sys.path.insert(0, str(source / "scripts"))
    legacy = importlib.import_module("qwen_long_history")
    from transformers import AutoTokenizer

    dev = read(run / "development.json")
    gold = {c["id"]: c for c in dev}
    selector_identity = read(run / "selector-identity.json")
    assert len(dev) == 7
    measured = read(run / "development-cost.json")
    assert measured["complete"] and measured["heldout_completed"] == 0
    tokenizer = AutoTokenizer.from_pretrained(
        read(previous / "rehearsal/registration.json")["config"]["backbone_directory"],
        local_files_only=True,
        trust_remote_code=False,
    )
    arms, raw = {}, {}
    sum_keys = (
        "prompt_tokens",
        "output_tokens",
        "selector_cpu_seconds",
        "selector_wall_seconds",
        "generation_cpu_seconds",
        "generation_wall_seconds",
        "request_cpu_seconds",
        "request_wall_seconds",
    )
    for arm in ("before", "lexical", "after"):
        internal = "lexical" if arm == "lexical" else "toruk"
        folder = run / "arms" / arm / "rehearsal"
        data = rows(folder / f"development-{internal}-answers.jsonl")
        assert len(data) == 8 and sum(not r["is_replay"] for r in data) == 7
        assert {r["id"] for r in data if not r["is_replay"]} == set(gold)
        traces = rows(folder / "selection-traces.jsonl")
        assert len(traces) == 8
        for row, trace in zip(data, traces, strict=True):
            case = gold[row["id"].removesuffix("-replay")]
            turns, selected = legacy.inference_turns(case), row["selected_indices"]
            assert row["selected_sources"] == [{"id": f"m{i}", **turns[i]} for i in selected]
            assert row["prompt_messages"] == legacy.envelope(turns, selected)
            ids = tokenizer.apply_chat_template(
                row["prompt_messages"], tokenize=True, add_generation_prompt=True, return_dict=False
            )
            assert row["prompt_ids"] == ids and row["prompt_tokens"] == len(ids) <= 512
            assert (
                tokenizer.decode(row["generated_ids"], skip_special_tokens=True).strip()
                == row["answer"]
            )
            assert row["score"] == legacy.score(row["answer"], case)
            assert row["failure"] == legacy.failure(row["score"], case, selected)
            assert row["required_evidence_retained"] == (set(case["required"]) <= set(selected))
            assert row["model"] == "Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf"
            assert selected == trace["selected_indices"]
            if arm == "after":
                assert row["selector_identity"] == selector_identity["runtime_identity_sha256"]
                older = set(row["proposed_indices"]) - set(range(len(turns) - 3, len(turns)))
                assert older <= set(trace["gate"]["admitted"])
        for key in ("answer", "score", "prompt_ids", "generated_ids", "selected_indices", "work"):
            assert data[-1][key] == data[0][key]
        if arm != "after":
            old = rows(previous / f"rehearsal/development-{internal}-answers.jsonl")
            for row, saved in zip(data, old, strict=True):
                for key in (
                    "answer",
                    "score",
                    "prompt_ids",
                    "generated_ids",
                    "selected_indices",
                    "work",
                    "selector_identity",
                ):
                    assert row[key] == saved[key], (arm, row["id"], key)
        ordinary = [r for r in data if not r["is_replay"]]
        raw[arm] = {r["id"]: r for r in ordinary}
        stage = next(s for s in measured["stages"] if s["v3_arm"] == arm)
        arms[arm] = {
            "correct": sum(r["score"]["correct"] for r in ordinary),
            "cases": 7,
            "known_evidence_retained": sum(
                r["required_evidence_retained"]
                for r in ordinary
                if gold[r["id"]]["expected"] != "UNKNOWN"
            ),
            "known_cases": 6,
            "replay_equal": True,
            "exact_copy": next(r["score"]["correct"] for r in ordinary if r["kind"] == "literal"),
            "preservation": next(
                r["score"]["correct"] for r in ordinary if r["kind"] == "preservation"
            ),
            "seven_case_costs": {k: sum(r[k] for r in ordinary) for k in sum_keys},
            "including_replay_costs": {k: sum(r[k] for r in data) for k in sum_keys},
            "stage_cpu_seconds": stage["cpu_seconds"],
            "stage_wall_seconds": stage["wall_seconds"],
            "sampled_private_peak_bytes": stage["peak_private_bytes"],
            "os_private_peak_bytes": stage["peak_os_private_bytes"],
            "worker": read(folder / f"development-{internal}-worker.json"),
            "failure": stage["failure"],
            "gate_term_calls_including_replay": sum(t["gate"]["gate_term_calls"] for t in traces)
            if arm == "after"
            else None,
            "gate_scan_bytes_including_replay": sum(t["gate"]["gate_scan_bytes"] for t in traces)
            if arm == "after"
            else None,
        }
    comparison = []
    for case in dev:
        item = {
            "id": case["id"],
            "kind": case["kind"],
            "expected": case["expected"],
            "question": case["messages"][-1]["content"],
            "required": case["required"],
        }
        for arm in ("before", "lexical", "after"):
            r = raw[arm][case["id"]]
            item[arm] = {
                k: r[k]
                for k in (
                    "answer",
                    "score",
                    "selected_indices",
                    "selected_sources",
                    "required_evidence_retained",
                    "prompt_tokens",
                    "selector_cpu_seconds",
                    "selector_wall_seconds",
                    "failure",
                )
            }
        assert (
            raw["before"][case["id"]]["work"]["selector_byte_positions"]
            == raw["after"][case["id"]]["work"]["selector_byte_positions"]
        )
        comparison.append(item)
    preserve = read(run / "preservation-before.json")
    for name, digest in preserve["bindings"].items():
        assert sha(Path(name)) == digest, name
    for item in preserve["metadata_only"]:
        stat = Path(item["path"]).stat()
        assert (stat.st_size, stat.st_mtime_ns) == (item["size"], item["mtime_ns"])
    criteria = {
        "technical_complete_and_controls_reproduced": True,
        "after_retains_all_known_evidence": arms["after"]["known_evidence_retained"] == 6,
        "after_improves_over_before": arms["after"]["correct"] > arms["before"]["correct"],
        "no_case_lost_against_lexical": all(
            not item["lexical"]["score"]["correct"] or item["after"]["score"]["correct"]
            for item in comparison
        ),
        "exact_copy": arms["after"]["exact_copy"],
        "preservation": arms["after"]["preservation"],
    }
    result = {
        "status": "DEVELOPMENT ONLY; no research/generalization verdict",
        "arms": arms,
        "criteria": criteria,
        "comparison": comparison,
        "heldout_completed": 0,
        "heldout_answers_opened": False,
        "new_training": False,
        "preserved_readable_files": len(preserve["bindings"]),
        "metadata_only_preservation_files": len(preserve["metadata_only"]),
        "registration_sha256": sha(run / "registration.json"),
        "selector_identity": selector_identity,
        "audit_wall_seconds": time.perf_counter() - start_wall,
        "audit_cpu_seconds": time.process_time() - start_cpu,
    }
    write(run / "results.json", result)
    print(
        json.dumps(
            {
                "correct": {a: r["correct"] for a, r in arms.items()},
                "criteria": criteria,
                "cases": [
                    {
                        "kind": c["kind"],
                        "expected": c["expected"],
                        **{
                            a: {
                                k: c[a][k]
                                for k in (
                                    "answer",
                                    "prompt_tokens",
                                    "selector_cpu_seconds",
                                    "selector_wall_seconds",
                                    "failure",
                                )
                            }
                            for a in ("before", "lexical", "after")
                        },
                    }
                    for c in comparison
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
