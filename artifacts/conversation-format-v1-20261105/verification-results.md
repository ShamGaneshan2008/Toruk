# Local verification evidence

Final full verify: PASS. Python: 232 passed. Node: 18 passed, one standalone live test skipped. Hosted CI was not observed.

Initial verification failures remain retained and are superseded by the complete stable-source final run. Initial Node wrapper stdout required explicit UTF-8 after tests had passed.

| Check | Status | Seconds | Log |
|---|---|---:|---|
| checks/bounded-training | PASS | 58.979 | [log](checks/bounded-training.log) |
| checks/chat-integration | PASS | 26.804 | [log](checks/chat-integration.log) |
| checks/controlled-cli-recheck | PASS | 16.093 | [log](checks/controlled-cli-recheck.log) |
| checks/diagnostic-equality | PASS | 2.221 | [log](checks/diagnostic-equality.log) |
| checks/diagnostic-replay | PASS | 67.333 | [log](checks/diagnostic-replay.log) |
| checks/environment | PASS | 2.48 | [log](checks/environment.log) |
| checks/final-diff | PASS | 0.078 | [log](checks/final-diff.log) |
| checks/final-format | PASS | 0.111 | [log](checks/final-format.log) |
| checks/final-integration | PASS | 20.449 | [log](checks/final-integration.log) |
| checks/final-lint | PASS | 0.108 | [log](checks/final-lint.log) |
| checks/frozen-evaluation | PASS | 98.577 | [log](checks/frozen-evaluation.log) |
| checks/historical-replay | PASS | 22.235 | [log](checks/historical-replay.log) |
| checks/node-check | PASS | 3.456 | [log](checks/node-check.log) |
| checks/node-tests-utf8 | PASS | 0.948 | [log](checks/node-tests-utf8.log) |
| checks/node-tests | PASS | 0.98 | [log](checks/node-tests.log) |
| checks/prepare | PASS | 4.572 | [log](checks/prepare.log) |
| checks/registration | PASS | 2.291 | [log](checks/registration.log) |
| verification/build | PASS | 4.921 | [log](verification/build.log) |
| verification/conversation-data | PASS | 2.266 | [log](verification/conversation-data.log) |
| verification/diagnose | PASS | 2.205 | [log](verification/diagnose.log) |
| verification/diff-check | FAIL | 0.065 | [log](verification/diff-check.log) |
| verification/format | PASS | 0.099 | [log](verification/format.log) |
| verification/frozen-sources | PASS | 0.071 | [log](verification/frozen-sources.log) |
| verification/help | PASS | 2.283 | [log](verification/help.log) |
| verification/import | PASS | 0.04 | [log](verification/import.log) |
| verification/independent-cases | PASS | 2.265 | [log](verification/independent-cases.log) |
| verification/install-local | PASS | 3.774 | [log](verification/install-local.log) |
| verification/lint | FAIL | 0.125 | [log](verification/lint.log) |
| verification/owned-lm-generate | PASS | 4.054 | [log](verification/owned-lm-generate.log) |
| verification/owned-lm-smoke | PASS | 5.456 | [log](verification/owned-lm-smoke.log) |
| verification/package | PASS | 0.843 | [log](verification/package.log) |
| verification/reproduce | PASS | 4.664 | [log](verification/reproduce.log) |
| verification/research-config | PASS | 2.449 | [log](verification/research-config.log) |
| verification/research-smoke | PASS | 5.098 | [log](verification/research-smoke.log) |
| verification/staged-diff-check | PASS | 0.034 | [log](verification/staged-diff-check.log) |
| verification/summarize | PASS | 4.162 | [log](verification/summarize.log) |
| verification/tests | FAIL | 142.913 | [log](verification/tests.log) |
| verification/types-linux | PASS | 46.663 | [log](verification/types-linux.log) |
| verification/types | PASS | 74.827 | [log](verification/types.log) |
| verification/validate | PASS | 2.426 | [log](verification/validate.log) |
| verification-final/build | PASS | 4.348 | [log](verification-final/build.log) |
| verification-final/conversation-data | PASS | 2.116 | [log](verification-final/conversation-data.log) |
| verification-final/diagnose | PASS | 2.275 | [log](verification-final/diagnose.log) |
| verification-final/diff-check | PASS | 0.08 | [log](verification-final/diff-check.log) |
| verification-final/format | PASS | 0.092 | [log](verification-final/format.log) |
| verification-final/frozen-sources | PASS | 0.07 | [log](verification-final/frozen-sources.log) |
| verification-final/help | PASS | 2.164 | [log](verification-final/help.log) |
| verification-final/import | PASS | 0.039 | [log](verification-final/import.log) |
| verification-final/independent-cases | PASS | 2.148 | [log](verification-final/independent-cases.log) |
| verification-final/install-local | PASS | 2.753 | [log](verification-final/install-local.log) |
| verification-final/lint | PASS | 0.094 | [log](verification-final/lint.log) |
| verification-final/owned-lm-generate | PASS | 3.666 | [log](verification-final/owned-lm-generate.log) |
| verification-final/owned-lm-smoke | PASS | 5.064 | [log](verification-final/owned-lm-smoke.log) |
| verification-final/package | PASS | 0.623 | [log](verification-final/package.log) |
| verification-final/reproduce | PASS | 4.078 | [log](verification-final/reproduce.log) |
| verification-final/research-config | PASS | 2.321 | [log](verification-final/research-config.log) |
| verification-final/research-smoke | PASS | 5.107 | [log](verification-final/research-smoke.log) |
| verification-final/staged-diff-check | PASS | 0.033 | [log](verification-final/staged-diff-check.log) |
| verification-final/summarize | PASS | 3.908 | [log](verification-final/summarize.log) |
| verification-final/tests | PASS | 141.882 | [log](verification-final/tests.log) |
| verification-final/types-linux | PASS | 46.599 | [log](verification-final/types-linux.log) |
| verification-final/types | PASS | 46.586 | [log](verification-final/types.log) |
| verification-final/validate | PASS | 2.195 | [log](verification-final/validate.log) |
