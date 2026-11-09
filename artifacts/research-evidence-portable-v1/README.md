# Portable frozen research evidence

Run `python scripts/verify_portable_research_evidence.py verify` from the checkout root. Install the existing optional chat dependencies for offline native-tokenizer checks. No backbone weights, network, training or generation are used. `--no-native` omits only native tokenization/decode verification and reports that limitation.

Historical files remain byte-identical. Recorded D:/Toruk and C-drive paths map to repository-relative paths; exact as-run source/checkpoint bytes can resolve through frozen ZIP members rather than the current source. No hash is repaired or normalized.

Excluded model downloads, caches, generated fixture models and all wheels/sdists remain local. Original broad manifests include those files; their omitted bindings are reported explicitly, so this is complete OFFLINE REPORT evidence, not a full original environment or a model-inference reproduction. Original check receipts/logs remain included. Tokenizers are verified byte copies of existing inputs, not regenerated evidence. The selector ZIP contains the primary trained checkpoint; one profile checkpoint covers both identical recorded profile weights.

Original frozen records contain machine paths and user-directory names. They are preserved for provenance, not redacted. Review before committing/sharing.
