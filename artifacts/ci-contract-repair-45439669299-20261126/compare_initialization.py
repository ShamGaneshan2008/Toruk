"""Compare saved diagnostics only; never import torch or construct a model."""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def compare(left, right):
    records = {}
    for key, a in left["cells"].items():
        b = right["cells"][key]
        differing = [name for name, tensor in a["tensors"].items()
                     if tensor["sha256"] != b["tensors"][name]["sha256"]]
        records[key] = dict(
            left_sha256=a["current_sha256"], right_sha256=b["current_sha256"],
            same_model_hash=a["current_sha256"] == b["current_sha256"],
            same_rng_before=a["rng_before"] == b["rng_before"],
            same_rng_after=a["rng_after"] == b["rng_after"],
            differing_tensors=differing,
            tensor_examples={name: dict(left=a["tensors"][name], right=b["tensors"][name])
                             for name in differing[:2]},
        )
    return records


def main():
    names = dict(
        local="initialization-local-windows-002.json",
        local_scalar="initialization-local-scalar-windows.json",
        ubuntu="initialization-hosted-ubuntu.json",
        ubuntu_scalar="initialization-hosted-scalar-ubuntu.json",
        windows="initialization-hosted-windows.json",
        windows_scalar="initialization-hosted-scalar-windows.json",
    )
    data = {key: json.loads((BASE / name).read_text(encoding="utf-8"))
            for key, name in names.items() if (BASE / name).exists()}
    pairs = [("local", "local_scalar"), ("ubuntu", "windows"),
             ("ubuntu_scalar", "windows_scalar"), ("ubuntu", "ubuntu_scalar"),
             ("windows", "windows_scalar"), ("local", "windows")]
    result = dict(
        sources={key: dict(path=names[key], runtime=value["runtime"],
                          cpu_capability=value["cpu_capability"],
                          override=value.get("cpu_capability_override"))
                 for key, value in data.items()},
        comparisons={a + "_vs_" + b: compare(data[a], data[b])
                     for a, b in pairs if a in data and b in data},
        model_work_performed=0,
    )
    (BASE / "initialization-comparison.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: {cell: {field: row[field] for field in
          ("same_model_hash", "same_rng_before", "same_rng_after")}
          for cell, row in value.items()} for key, value in result["comparisons"].items()}))


if __name__ == "__main__":
    main()
