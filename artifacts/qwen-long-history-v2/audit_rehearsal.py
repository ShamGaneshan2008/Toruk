"""Offline audit only: tokenize and score saved development rows; never generate."""

import hashlib
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("D:/Toruk")
RUN = ROOT / "artifacts/qwen-long-history-v2/attempt-003"
sys.path.insert(0, str(SOURCE / "scripts"))
import qwen_long_history as legacy
from transformers import AutoTokenizer

started, used = time.perf_counter(), time.process_time()


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")


frozen = read(RUN / "proposed-freeze.json")
for bindings in (frozen["registered_inputs"], frozen["output_bindings"]):
    for name, digest in bindings.items():
        assert sha(Path(name)) == digest, name
registration = read(RUN / "rehearsal/registration.json")
cases = read(RUN / "rehearsal/development.json")
gold = {case["id"]: case for case in cases}
tokenizer = AutoTokenizer.from_pretrained(
    registration["config"]["backbone_directory"], local_files_only=True, trust_remote_code=False
)
arms = {}
for arm in legacy.ARMS:
    path = RUN / f"rehearsal/development-{arm}-answers.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    original = [row for row in rows if not row["is_replay"]]
    assert len(rows) == 8 and {row["id"] for row in original} == set(gold)
    for row in rows:
        case = gold[row["id"].removesuffix("-replay")]
        turns = legacy.inference_turns(case)
        indices = row["selected_indices"]
        assert row["selected_sources"] == [{"id": f"m{i}", **turns[i]} for i in indices]
        assert row["prompt_messages"] == legacy.envelope(turns, indices)
        ids = tokenizer.apply_chat_template(
            row["prompt_messages"], tokenize=True, add_generation_prompt=True, return_dict=False
        )
        assert ids == row["prompt_ids"]
        assert row["prompt_tokens"] == len(ids)
        assert row["output_tokens"] == len(row["generated_ids"])
        assert tokenizer.decode(row["generated_ids"], skip_special_tokens=True).strip() == row["answer"]
        assert row["score"] == legacy.score(row["answer"], case)
        assert row["failure"] == legacy.failure(row["score"], case, indices)
        assert row["required_evidence_retained"] == (set(case["required"]) <= set(indices))
        assert len(ids) <= (32704 if arm == "full" else 512)
        assert row["work"]["backbone_positions"] == len(ids) + len(row["generated_ids"]) - 1
        assert row["model"] == "Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf"
    for key in ("answer", "score", "prompt_ids", "generated_ids", "selected_indices", "work"):
        assert rows[-1][key] == rows[0][key]
    cost = read(RUN / f"rehearsal/development-{arm}-v2-cost.json")
    heartbeats = [json.loads(line) for line in (
        RUN / f"rehearsal/development-{arm}-heartbeats.jsonl").read_text().splitlines()]
    arms[arm] = {
        "correct": sum(row["score"]["correct"] for row in original),
        "completed": len(original), "replay_count": 1, "replay_equal": True,
        "exact_copy": {"correct": sum(row["score"]["correct"] for row in original if row["kind"] == "literal"), "n": 1},
        "preservation": {"correct": sum(row["score"]["correct"] for row in original if row["kind"] == "preservation"), "n": 1},
        "categories": {k: {"correct": sum(row["score"]["correct"] for row in original if row["kind"] == k), "n": 1} for k in legacy.KINDS},
        "prompt_tokens_including_replay": sum(row["prompt_tokens"] for row in rows),
        "output_tokens_including_replay": sum(row["output_tokens"] for row in rows),
        "selector_cpu_seconds": sum(row["selector_cpu_seconds"] for row in rows),
        "selector_wall_seconds": sum(row["selector_wall_seconds"] for row in rows),
        "generation_cpu_seconds": sum(row["generation_cpu_seconds"] for row in rows),
        "generation_wall_seconds": sum(row["generation_wall_seconds"] for row in rows),
        "stage_cpu_seconds": cost["cpu_seconds"], "stage_wall_seconds": cost["wall_seconds"],
        "sampled_peak_private_GiB": cost["peak_private_bytes"] / 1024 ** 3,
        "sampled_peak_rss_GiB": cost["peak_rss_bytes"] / 1024 ** 3,
        "observed_os_private_peak_GiB": cost["peak_os_private_bytes"] / 1024 ** 3,
        "elapsed_minus_awake_seconds": cost["wall_seconds"] - (cost["end"]["awake_seconds"] - cost["start"]["awake_seconds"]),
        "max_flushed_heartbeat_monitor_gap_seconds": max(h["monitor_gap_seconds"] for h in heartbeats),
        "failure": cost["failure"],
    }
assert not list((RUN / "rehearsal").glob("heldout*"))
assert not list((SOURCE / "artifacts/qwen-long-history-v1/execution-v2").glob("heldout-*"))
preservation = read(RUN / "preservation-before.json")
for name, digest in preservation["bindings"].items():
    assert sha(Path(name)) == digest, name
for item in preservation["unreadable"]:
    stat = Path(item["path"]).stat()
    assert (stat.st_size, stat.st_mtime_ns) == (item["size"], item["mtime_ns"])
write(RUN / "offline-audit.json", {
    "status": "PASS", "no_generation": True, "development_only": True,
    "proposed_freeze_sha256": sha(RUN / "proposed-freeze.json"),
    "arms": arms, "heldout_completed": {arm: 0 for arm in legacy.ARMS},
    "readable_preservation_files_checked": len(preservation["bindings"]),
    "metadata_only_preservation_files": len(preservation["unreadable"]),
    "audit_wall_seconds_after_imports": time.perf_counter() - started,
    "audit_cpu_seconds_after_imports": time.process_time() - used,
    "runtime": {"python": sys.version, "platform": platform.platform(),
                "distributions": {n: importlib.metadata.version(n) for n in registration["dependencies"]}},
})
print(json.dumps({"status": "PASS", "arms": arms, "heldout_completed": 0}, indent=2))
