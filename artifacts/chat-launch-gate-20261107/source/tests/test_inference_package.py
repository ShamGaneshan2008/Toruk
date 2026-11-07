"""The deployment allowlist must contain every transitive Toruk runtime import."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_inference_package import MODULES  # noqa: E402


def test_inference_allowlist_is_closed_over_project_imports():
    missing = set()
    for module in MODULES:
        tree = ast.parse((ROOT / "src/toruk_lm" / f"{module}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("toruk_lm.")
            ):
                dependency = node.module.split(".")[1]
                if dependency not in MODULES:
                    missing.add(dependency)
    assert not missing, f"Published inference package would miss imports: {sorted(missing)}"
