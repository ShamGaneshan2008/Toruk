"""Disposable initialization diagnostics; no training, checkpoint loads or answers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any

from ci_contracts import ROOT, check_probe_checkpoints, read, runtime_identity


def diagnose() -> dict[str, Any]:
    import torch
    from answer_trainability_dev import PARAMETERS, initial_hash, make_model

    from toruk_lm.engine import setup

    cells = {}
    for seed in (601, 947):
        for variant in PARAMETERS:
            setup(seed, 1)
            before = hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest()
            model = make_model(variant)
            state = {}
            for name, value in model.state_dict().items():
                state[name] = dict(
                    shape=list(value.shape),
                    dtype=str(value.dtype),
                    sha256=hashlib.sha256(value.detach().numpy().tobytes()).hexdigest(),
                    first_values=value.detach().reshape(-1)[:4].tolist(),
                )
            digest = initial_hash(model)
            after = hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest()
            setup(seed, 1)
            repeated = make_model(variant)
            if initial_hash(repeated) != digest:
                raise ValueError("same-runtime seeded initialization is not repeatable")
            if sum(p.numel() for p in model.parameters()) != PARAMETERS[variant]:
                raise ValueError("model parameter contract changed")
            recorded = read(
                ROOT
                / "artifacts/local-answer-dev-v1/stages"
                / f"train-{seed}-{variant}/training-summary.json"
            )["initial_sha256"]
            cells[f"{seed}-{variant}"] = dict(
                current_sha256=digest,
                recorded_sha256=recorded,
                equals_recorded=digest == recorded,
                same_runtime_repeatable=True,
                rng_before=before,
                rng_after=after,
                tensors=state,
            )
    return dict(
        runtime=runtime_identity(),
        frozen_runtime=read(ROOT / "artifacts/local-answer-dev-v1/registration.json")["runtime"],
        cpu_capability=torch.backends.cpu.get_cpu_capability(),
        cpu_capability_override=os.environ.get("ATEN_CPU_CAPABILITY"),
        machine=platform.machine(),
        torch_build=torch.__config__.show(),
        cells=cells,
        scope=(
            "Current-runtime initialization only; "
            "not cross-runtime byte identity or research reproduction"
        ),
        optional_local_checkpoints=check_probe_checkpoints(),
        optimizer_updates=0,
        model_forwards=0,
        answers_generated=0,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("INITIALIZATION_CONTRACT=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
