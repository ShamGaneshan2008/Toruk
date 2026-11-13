"""Account for post-study verification separately; no study cells are rerun."""
import subprocess
import sys
import time
from pathlib import Path

started = time.perf_counter()
root = Path(__file__).resolve().parent
repo = root.parents[1]
sys.path.insert(0, str(repo / "scripts"))
from segment_delta_watch import worker_receipt

result = subprocess.run([sys.executable, "scripts/verify_segment_delta_dev.py", "--output-dir",
                         str(root.parent / "segment-delta-dev-v1-verification-001")], cwd=repo,
                        timeout=840)
worker_receipt(root.parent / "segment-delta-dev-v1-verification-cost-001", started, 0.)
sys.exit(result.returncode)
