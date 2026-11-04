"""Isolated wheel install; reuse installed dependencies explicitly, never the editable package."""

import argparse
import json
import subprocess
import sys
import sysconfig
import tarfile
import venv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--sdist", type=Path)
    args = parser.parse_args()
    if not args.wheel.is_file() or args.output.exists():
        parser.error("existing wheel and fresh output directory required")
    if args.sdist:
        with tarfile.open(args.sdist) as archive:
            names = archive.getnames()
        required = (
            "configs/reproduce-smoke-v1.json",
            "configs/reproduce-primary-v1.json",
            "scripts/verify.py",
            "docs/reproducibility.md",
        )
        if any(not any(name.endswith("/" + suffix) for name in names) for suffix in required):
            parser.error("sdist is missing reproduction configs, scripts or instructions")
        if any("/docs/internal/" in name for name in names):
            parser.error("sdist unexpectedly includes unreleased internal documents")
    env_path = args.output.resolve() / "env"
    venv.EnvBuilder(with_pip=False).create(env_path)
    python = env_path / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "--python",
            str(python),
            "install",
            "--no-index",
            "--no-deps",
            str(args.wheel.resolve()),
        ],
        check=True,
        timeout=60,
    )
    site = subprocess.check_output(
        [str(python), "-I", "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        text=True,
        timeout=30,
    ).strip()
    # A path-only .pth adds dependency modules without executing the donor's editable .pth.
    (Path(site) / "shared_dependencies.pth").write_text(
        sysconfig.get_paths()["purelib"] + "\n", encoding="utf-8"
    )
    script = (
        "import json, pathlib, sys, toruk_lm; "
        "p=pathlib.Path(toruk_lm.__file__).resolve(); "
        "assert p.is_relative_to(pathlib.Path(sys.prefix)); "
        "print(json.dumps({'package_file':str(p),'version':toruk_lm.__version__}))"
    )
    commands = [
        [str(python), "-I", "-c", script],
        [str(python), "-I", "-m", "toruk_lm", "--help"],
        [str(python), "-I", "-m", "toruk_lm", "diagnose"],
        [
            str(python),
            "-I",
            "-m",
            "toruk_lm",
            "validate-config",
            "--config",
            str(args.config.resolve()),
        ],
        [
            str(python),
            "-I",
            "-m",
            "toruk_lm",
            "reproduce",
            "--config",
            str(args.config.resolve()),
            "--output",
            str(args.output.resolve() / "smoke"),
        ],
    ]
    for command in commands:
        print(json.dumps(dict(command=command)), flush=True)
        subprocess.run(command, check=True, timeout=120)
    result = dict(
        status="PASS",
        isolation=(
            "fresh venv and installed wheel; dependencies shared by explicit path; "
            "no editable package"
        ),
        dependency_fresh_install="NOT_RUN; no network dependency provisioning",
        commands=commands,
    )
    (args.output / "installation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
