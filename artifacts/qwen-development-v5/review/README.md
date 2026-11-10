# Preservation review: completed v5 negative result

The three registered instruction conditions remain original, field and check,
each applied to Toruk and lexical. Their accuracy is respectively 5/7 versus
7/7, 5/7 versus 4/7, and 5/7 versus 5/7. Both candidates fail the registered
improvement, no-new-loss and evidence/exact-copy/preservation combined gates.
The technical and no-loss-versus-matched-lexical gates pass; the latter does not
offset degradation of lexical. Neither candidate supports a production change.

All original 189 v5 files, including failed preflights, both source archives,
registered config/protocol/runner/tests, report, raw answers, costs and check
receipts, remain byte-identical. `../evidence-manifest.json` still binds its
original 188 payloads. Its own bytes are also inventoried by this review.
The original report and verification summary describe the study's pre-commit
state; those historical references to uncommitted files and HEAD `0705a3d` are
preserved rather than rewritten as if a commit had already existed. The user's
subsequent instruction authorizes committing this completed v5 study on main.
The protocol's historical request to leave that original work uncommitted is
superseded for this preservation step. No v6 or new inference is authorized here.

## File, credential and path review

`file-review.json` records a review of every original prospective file, including
all JSON/JSONL structures and 98 exact source ZIP members. Archive integrity and
member paths were checked. All paths belong to v5 or its four specifically
scoped Git attribute additions. The source archives contain only registered
source/config/protocol/test bytes and inherited source; they contain no model
weights, build, cache or held-out case files. Generated engineering fixture
directories, caches and wheels/sdists remain local and ignored. Original failed
engineering checks are retained because they document the preparation history.

No private keys, AWS/GitHub/OpenAI/Slack credential patterns, authenticated URLs,
or literal credential assignments were found. This is a pattern scan plus
content review, not a guarantee against every possible encoding of a secret.
Personal paths were found in 20 original files/archive members: the username
`susee`, the original `C:/Users/susee/VS_CODE_PROJECT/Toruk` checkout and temporary
user-directory locations, plus workspace paths such as `D:/Toruk`. These are
historical machine provenance, not credentials. They are retained explicitly so
registered hashes, logs and costs remain auditable. Nothing is pushed or sent
to a remote service by this review. Review that disclosure before a later push.

## Offline portable checks

The new `../verify.py` validates the original payload manifest, 596 frozen hashes,
local registration bindings, recorded external-asset identities and resource
totals, then replays the sealed runner's native development audit in memory.
It reproduces all substantive result fields, including prompt/output IDs,
answers, frozen scores, selection/replay checks, exact-copy/preservation results,
costs and failed decision gates. Only newly measured audit CPU/wall timing is
excluded. It does not load backbone or selector weights or generate any answers.
External asset identities are checked against the original registration; their
omitted bytes and original host execution are not reproduced. No absolute
machine path is needed for this offline result audit. Inherited held-out files
are hashed only and are never parsed or scored.

From the repository root, with the existing chat/development dependencies:

```powershell
.venv/Scripts/python.exe artifacts/qwen-development-v5/verify.py
.venv/Scripts/python.exe artifacts/qwen-development-v5/verify.py --staged
.venv/Scripts/python.exe artifacts/qwen-long-history-dev-v4/verify.py --staged
.venv/Scripts/python.exe -m pytest -q tests/test_qwen_development_v5.py tests/test_qwen_development_v4.py tests/test_qwen_long_history_v3.py tests/test_qwen_long_history_v2.py tests/test_qwen_long_history.py artifacts/qwen-development-v5/test_verify.py
git diff --check
git diff --cached --check
```

The broader portable-v1 answer verifier remains excluded because it also
rescores historical held-out answers. No frozen v1-v4 source/evidence is edited.
The new verifier has focused path, corruption, external-binding and replay
comparison contracts. Its initial test exposed Windows drive-relative rooted
paths (`/outside`); rejecting any path anchor corrected the guard before staged
verification. The initial failing receipt is retained. This change is solely
in publication auditing; registered inference code and results remain unchanged.
Git exports may change default text checkout newlines. The verifier accepts LF
or CRLF restoration only when the entire historical SHA-256 matches, lists each
substitution, and never rewrites a file or hash. A focused test checks that rule.

Review check receipts remain in `checks/`; original study verification records
remain in their original locations. No production chat files are staged.
