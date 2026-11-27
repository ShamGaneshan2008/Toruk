"""Run the independent saved-only auditor inside a measured, observer-sealed Job."""

import json
import os
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
DIRECTORY = Path(sys.argv[1]).resolve()
assert DIRECTORY.is_relative_to(RUN) and DIRECTORY.is_dir()


def guard(event, args):
    if event == "import" and args[0].split(".")[0] in {
        "torch", "transformers", "ollama", "toruk_lm", "city_contrastive_dev"
    }:
        raise RuntimeError("Independent audit cannot import model/training code")
    if event != "open" or isinstance(args[0], int):
        return
    path = Path(args[0]).resolve()
    if any(s in str(path).lower() for s in ("heldout", "held-out", "held_out")):
        raise RuntimeError("Held-out access forbidden")
    writing = (args[2] or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
    if writing and (not path.is_relative_to(RUN) or path.is_relative_to(RUN / "registered")):
        raise RuntimeError("Audit cannot write historical or sealed scientific evidence")


sys.addaudithook(guard)
sys.path.insert(0, str(ROOT / "scripts"))
import audit_city_contrastive_dev as independent  # noqa: E402
from lifetime_job import controller_record  # noqa: E402

with controller_record(DIRECTORY):
    try:
        result = independent.audit()
    except Exception as error:
        result = independent.partial_audit(error)
    for path in (RUN / "independent-audit.json", DIRECTORY / "audit.json"):
        with path.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("cells", "costs")},indent=2))
