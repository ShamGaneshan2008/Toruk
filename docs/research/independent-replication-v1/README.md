# Toruk exploratory replication package

**Verdict: the central lower-cost/quality-preserving claim is not established.**
The independent frozen-rubric score is 9/24 for Toruk versus 6/24 for lexical
retrieval, but Toruk uses 33.1% more model tokens and 19.7% more request time.
Its paired quality interval includes zero. The package is a local exploratory
draft and evidence bundle, not a submitted paper or verified positive result.

- [Measured results, failures and verification](../independent-replication-v1-results.md)
- [Draft with implemented architecture diagram](draft.md)
- [Claim ledger](claim-ledger.md) and [machine-readable ledger](claim-ledger.json)
- [Windows PowerShell and CI reproduction](reproduce.md)
- [Primary-source positioning and search record](positioning.md)
- [Bibliography](references.bib)
- [Frozen protocol](../independent-replication-v1-protocol.md)
- [Raw evidence and checks](../../../artifacts/independent-replication-20261104/)

Pretrained Qwen supplies language generation. Toruk contributes the historically
trained eight-feature turn scorer, bounded selection and source presentation.
This study changes none of those weights or mechanism thresholds. It freshly
reproduces the previous milestone, then evaluates 24 separately authored cases
and three actual-component ablations on both datasets. No externally independent
investigator or human semantic adjudicator participated.

The replication overlay archive targets base commit
`84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`. It includes required uncommitted
source/config/docs, raw evidence and small pinned backbone support files. The
pretrained weight file and generated training checkpoints are excluded; obtain
the pinned weights using the reproduction guide. Nothing was committed, pushed,
published or deployed. Hosted CI for this work remains unobserved.
