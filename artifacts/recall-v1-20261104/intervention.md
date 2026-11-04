# Decision after the full development-only before run

Old selector: 7/12 correct, with five failed cases despite retained required
evidence: quote, correction, gist, gist_correction, ambiguous. All five are
reproduced as failures by lexical selection as well. Recent context is 2/12.
This motivates evidence presentation rather than a new trained retriever.

One intervention: quote the old selected source turns in one chronological
transcript with role/span labels and a generic instruction to copy exact strings,
apply explicit corrections, preserve unrelated facts and clarify ambiguity.
The old ranker and model weights are unchanged. Labels and expected answers are
not supplied. No record parser, answer lookup, persistent memory or second model.
This is a prompt serialization intervention, not learned compressed gist memory.

The study's original driver and scoring stay byte-sealed. recall_after.py injects
the additive backend subclass before invoking that same driver. Freeze both files
with the new module/tests before new development and heldout inference. The source
envelope is research-only; chat server, browser path and checkpoint loader stay
unchanged. Negative results and any regressions must remain in the report.
