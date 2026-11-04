# Recall milestone CI integration — 4 November 2026

The CPU foundation workflow runs on push, pull request and manual dispatch, with
separate Node/web and Python jobs. No deployment/CD job is configured. The recall
research report retains its original local/remote statuses as historical evidence.

The previous Python CI blocker was 49 lint findings and formatting differences
in three byte-frozen v2 experiment scripts. Those sources remain unchanged.
Narrow per-file lint exceptions cover their recorded E501/F401 findings, and the
formatter excludes only those three archived files. All other lint rules still
apply. A new mandatory workflow step verifies their exact SHA256 values from
`configs/frozen-source-sha256.json`; tests confirm both acceptance and rejection
of modified bytes. The local verification driver runs the same guard.

New recall evidence/source files have explicit Git attributes preserving their
registered bytes across Windows/Linux checkouts. Private notes and ignored model
weights are excluded from publication. New research results remain negative; CI
integration does not qualify memory accuracy or efficiency.

The local verifier now writes package outputs into its own fresh run directory,
avoiding collisions with the existing protected dist archives. Local commands,
exit codes and source fingerprints are retained under
`artifacts/checks/recall-ci-integration-20261104/`. Remote Actions must be assessed
against the exact pushed commit, separately from these local observations.

Local validation: 185 Python tests pass, full repository Ruff/format pass,
runtime mypy passes for Windows and Linux, Node syntax/tests pass (13 tests,
one optional live skip), and CLI ordinary/recurrent smoke and package checks
pass. The verifier process was launched before its build-output edit, so its
loaded old default-dist build command still failed on the protected archive;
that failure is retained in build.log. The separately recorded build-fresh
command succeeds with the final fresh-output arguments. Git diff checks pass.
Rebuildable distribution binaries remain local; text evidence is published.

The first pushed commit, `94d11797355b3373fa2ff7547415676d52ad4c07`, passed
remote web, frozen-source, lint and format checks. Actions run 41802844536 then
exposed a missing optional Transformers dependency in mypy: the runner installed
only `.[dev]`, while local checks had chat dependencies available. The workflow
now installs `.[dev,chat]` so the checked chat imports have their dependencies.
This installs libraries, not model weights. The first failure is retained in
`artifacts/checks/recall-ci-integration-20261104/first-remote-failure.json`.
