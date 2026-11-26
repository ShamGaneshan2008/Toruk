"""Strict offline hashes for optional original probe weights; missing inputs exit 2."""

import json

from ci_contracts import check_probe_checkpoints


def main() -> None:
    result = check_probe_checkpoints()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(
        0 if result["status"] == "PASS" else 2 if result["status"] == "MISSING_INPUTS" else 1
    )


if __name__ == "__main__":
    main()
