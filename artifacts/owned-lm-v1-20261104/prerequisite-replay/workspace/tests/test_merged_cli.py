"""The merged CLI must retain both reproduction protocols without ambiguity."""

import subprocess
import sys

from toruk_lm.cli import parser


def test_reproduce_has_one_parser_and_retains_foundation_options():
    args = parser().parse_args(["reproduce", "--output", "fresh", "--steps", "3"])
    assert args.steps == 3 and args.config is None
    args = parser().parse_args(
        ["reproduce", "--config", "configs/reproduce-smoke-v1.json", "--output", "fresh"]
    )
    assert args.steps is None and args.documents is None


def test_versioned_reproduction_rejects_foundation_overrides(tmp_path):
    output = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "toruk_lm",
            "reproduce",
            "--config",
            "configs/reproduce-smoke-v1.json",
            "--steps",
            "80",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "do not accept protocol overrides" in result.stderr
    assert "Traceback" not in result.stderr
    assert not output.exists()
