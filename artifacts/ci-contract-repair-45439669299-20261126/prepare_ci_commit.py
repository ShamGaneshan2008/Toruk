"""Build a scoped CI commit with an isolated index; do not change main or push."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

from prepare_fresh_clone import FILES, ROOT

BASE = Path(__file__).resolve().parent
HEAD = "31da24ea2c876b75f63ae537f499f73df86129e9"
BRANCH = "ci/repair-cpu-foundation-45439669299-20261126"


def main():
    def git(*args, **kwargs):
        return subprocess.check_output(["git", *args], cwd=ROOT, **kwargs).decode().strip()

    assert git("rev-parse", "HEAD") == HEAD
    assert not git("diff", "--cached", "--name-only")
    index = ROOT / ".git" / "ci-contract-repair-45439669299.index"
    assert not index.exists()
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    git("read-tree", HEAD, env=env)
    git("add", "--", *FILES, env=env)
    git("diff", "--cached", "--check", env=env)
    names = git("diff", "--cached", "--name-only", env=env).splitlines()
    assert set(names) == set(FILES)
    tree = git("write-tree", env=env)
    commit = git(
        "commit-tree", tree, "-p", HEAD,
        input=b"Repair platform and archived-input CI contracts\n\nTemporary CI-only validation; frozen research evidence unchanged.\n",
    )
    assert git("rev-parse", "HEAD") == HEAD
    assert not git("diff", "--cached", "--name-only")
    packet = dict(
        parent=HEAD, commit=commit, branch=BRANCH,
        main_unchanged=True, pushed=False,
        files={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES},
    )
    with (BASE / "ci-commit.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(packet, stream, indent=2)
        stream.write("\n")
    print(json.dumps(packet, indent=2))


if __name__ == "__main__":
    main()
