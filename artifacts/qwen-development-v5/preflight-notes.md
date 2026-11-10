# V5 pre-inference preparation record

No inference ran from attempt-001. Its registration and exact source ZIP remain
unchanged. The explicit script Mypy preflight failed on dynamic module adapters;
adding `typing.cast(Any, ...)` makes their research-only replacement explicit to
the checker without changing their runtime behavior. The corrected check passes.
Attempt-002 seals that corrected source before any generation. Both attempts use
the identical candidate config/protocol/tests and frozen scientific inputs.

The first manual Ruff pass also exposed formatting and an implicit non-strict
zip in partial-result auditing. These were corrected before attempt-001. The
focused preflight passed 82 tests; an existing unwritable pytest cache produced
a warning without changing test outcomes. Check receipts retain the Mypy failure
and correction, registration costs and portable verification result. Preparation
costs for both registrations must be disclosed; neither registration generated
answers. There are no inference retries or post-answer prompt revisions.

The first final whitespace wrapper treated `git diff --no-index --check` exit 1
as a whitespace failure. In no-index mode that code also means a new-file
difference with no diagnostic. The corrected wrapper accepts 0/1 only when both
output streams are empty; it also suppresses automatic newline-conversion
warnings through a process-local Git option. It passes all 183 then-present new
text files. Both receipts remain. No source or evidence bytes were changed to
make the check pass; ordinary `git diff --check` passed separately.
