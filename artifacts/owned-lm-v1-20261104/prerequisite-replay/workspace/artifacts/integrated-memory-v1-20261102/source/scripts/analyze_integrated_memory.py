"""Post-evaluation analysis only; never changes or reruns the frozen answer scorer."""

import argparse
import json
from pathlib import Path
from typing import Any

import torch

from toruk_lm.data import sha256_file, write_json
from toruk_lm.integrated_memory import load_integrated, padded, text_tokens
from toruk_lm.integrated_study import read_data, verify_seal


def analyze(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "format": "toruk-integrated-analysis-v1",
        "seeds": {},
        "posthoc_routing_diagnostic": True,
    }
    torch.set_num_threads(1)
    rows = read_data(root / "data", "final")
    for seed in (31, 47):
        evaluations = {
            mode: json.loads((root / "final" / f"{mode}-{seed}.json").read_text())
            for mode in ("ordinary", "integrated", "external", "zero")
        }
        current: dict[str, Any] = {"methods": {}}
        for mode, evaluation in evaluations.items():
            predictions = evaluation["predictions"]
            training_variant = "ordinary" if mode in ("ordinary", "external") else "integrated"
            training = json.loads((root / "train" / f"{training_variant}-{seed}.json").read_text())
            current["methods"][mode] = {
                **evaluation["totals"],
                "peak_process_bytes": evaluation["peak_process_bytes"],
                "evaluation_process_seconds": json.loads(
                    (root / "checks" / f"final-{mode}-{seed}.json").read_text()
                )["seconds"],
                "training_seconds": training["training_seconds"],
                "training_peak_process_bytes": training["training_peak_process_bytes"],
                "parameters": training["parameters"],
                "checkpoint_sha256": evaluation["checkpoint_sha256"],
                "known_correct": sum(p["correct"] for p in predictions if p["expected"] != "?"),
                "known_cases": sum(p["expected"] != "?" for p in predictions),
                "state_bytes": predictions[0]["state_bytes"],
                "obsolete_answers": sum(p["obsolete_answer"] for p in predictions),
            }
        ordinary = {p["id"]: p for p in evaluations["ordinary"]["predictions"]}
        integrated = evaluations["integrated"]["predictions"]
        current["examples"] = {}
        predicates = {
            "gain": lambda p, baseline=ordinary: p["correct"] and not baseline[p["id"]]["correct"],
            "regression": lambda p, baseline=ordinary: (
                not p["correct"] and baseline[p["id"]]["correct"]
            ),
            "preservation_failure": lambda p: p["category"] == "preservation" and not p["correct"],
            "unsupported": lambda p: p["unsupported"],
        }
        for name, predicate in predicates.items():
            examples = [p for p in integrated if predicate(p)]
            current["examples"][name] = [
                {
                    "id": p["id"],
                    "query": p["query"],
                    "expected": p["expected"],
                    "integrated": p["answer"],
                    "ordinary": ordinary[p["id"]]["answer"],
                }
                for p in examples[:3]
            ]
        checkpoint = root / "train" / f"integrated-{seed}.pt"
        verify_seal(root / "freeze.json", checkpoint, root / "data", None)
        model, _ = load_integrated(checkpoint)
        read_correct = write_correct = write_count = 0
        diagnostic_rows = []
        with torch.no_grad():
            for row in rows:
                query = padded([text_tokens(row["query"], model.config.query_tokens)])
                read_key = int(model.read_address(model.encode(query)).argmax().item())
                read_correct += read_key == row["query_key"]
                correct = 0
                for event in row["events"]:
                    tokens = padded([text_tokens(event["text"], model.config.record_tokens)])
                    predicted = int(model.write_address(model.encode(tokens)).argmax().item())
                    correct += predicted == event["address"]
                    write_count += 1
                write_correct += correct
                diagnostic_rows.append(
                    {
                        "id": row["id"],
                        "read_predicted": read_key,
                        "read_expected": row["query_key"],
                        "write_correct": correct,
                        "writes": len(row["events"]),
                    }
                )
        current["routing"] = {
            "read_correct": read_correct,
            "read_cases": len(rows),
            "write_correct": write_correct,
            "write_cases": write_count,
            "rows": diagnostic_rows,
            "interpretation": (
                "Offline argmax diagnostics use gold addresses only for scoring; "
                "no answer is regenerated with gold state or addresses."
            ),
        }
        result["seeds"][str(seed)] = current
    result["freeze_sha256"] = sha256_file(root / "freeze.json")
    result["verdict"] = {
        "mechanism": "Implemented; CPU train/reload/resume and state influence verified.",
        "known_facts": (
            "Small observed gains on known facts in both seeds, with very low "
            "absolute correctness; no robust useful-memory claim."
        ),
        "correction_preservation": (
            "Failed; preservation 0/16 and 1/16, with more unsupported answers."
        ),
        "total_cost": "Failed; state updates increase forwarded work and full-history latency.",
        "paper_result": (
            "Insufficient; finite symbols, two training seeds, one final world seed, "
            "template-transfer failures."
        ),
        "chatbot": (
            "Still uses a separate pretrained Qwen/Ollama backbone; "
            "this prototype is research-only."
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh analysis output")
    result = analyze(args.run)
    write_json(args.output, result)
    for seed, values in result["seeds"].items():
        print(
            seed,
            {
                mode: (item["correct"], item["known_correct"], item["unsupported"])
                for mode, item in values["methods"].items()
            },
        )
        print("routing", {key: value for key, value in values["routing"].items() if key != "rows"})


if __name__ == "__main__":
    main()
