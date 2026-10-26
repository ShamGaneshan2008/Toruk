# Language-model capability follow-up — 2026-10-26

**Conclusion: basic LM behavior demonstrated, narrowly.** The ordinary causal model learned a held-out four-byte periodic next-token rule. The older ordinary-text and controlled-world runs remain pipeline smoke; neither demonstrates useful natural-language generation or factual answering. This report supersedes the capability conclusion in `language-model-capability-check.md` only for that small synthetic rule.

## State and evidence

Root `C:\Users\susee\VScode Project\Toruk`, branch `main`, commit `add917398efa061cc67b1b10aff3853acf3c526c`. At start, tracked files were clean and many prior artifacts/research notes, including the minimal demo, were untracked. Git warned that several older artifact directories were unreadable. All existing work was preserved; no reset, clean, stash, commit, push, publication, or training was done in this check. This report is the only new file.

I read the earlier [capability check](language-model-capability-check.md), [demo report](minimal-language-model-demo.md), frozen [demo protocol](../../artifacts/minimal-lm-demo-001/protocol.md), both configs, implementation and tests, then checked source and artifacts directly. The demo train and validation documents are distinct by ID and full text; their shared `abc ` pattern is intentional. The checkpoint's dataset hashes match the files on disk. The model has 12,112 parameters; checkpoint step is 120 and its SHA-256 is `e00a0f0b58233bc6013622e964c68eb9672db158bff80f0efdfceb5483e8b545`.

## One-example path and checks

- **Text → IDs:** `artifacts/minimal-lm-demo-001/data/{train,validation}.jsonl` holds `"abc " * n + "a"` (train n=8..15; validation n=16..17). [ByteTokenizer](../../src/toruk_lm/tokenizer.py) maps BOS=1, EOS=2 and UTF-8 bytes to 3..258 in a 259-ID vocabulary. Direct validation-window inspection found IDs 1..102, inside the vocabulary.
- **Targets → loss:** [windows and batch](../../src/toruk_lm/data.py) create nonoverlapping `x=tokens[:-1]`, `y=tokens[1:]` slices with -100 padding targets. [CausalLM and loss_sum](../../src/toruk_lm/model.py) use causal attention and valid-target cross entropy. The shift, causality, padding, and gradient tests pass. [train](../../src/toruk_lm/engine.py) updates only from its train path; validation is evaluated without updates. ID/exact-text overlap is rejected. The CLI without a manifest cannot prove semantic independence of arbitrary user-labelled splits, but the files and saved hashes in this run show no full-document overlap or validation-file training.
- **Checkpoint → generation → decoding:** [load_checkpoint/load_model](../../src/toruk_lm/engine.py) verify format, tokenizer fingerprint, dimensions, state and finite weights. [generate](../../src/toruk_lm/model.py) recomputes a bounded local context, suppresses PAD/BOS, and stops at EOS or the token cap. The tokenizer decodes byte IDs and ignores special IDs. Direct reload generated `abc abc abc abc ` from prompt `abc ` in 16 tokens; the saved CLI output agrees.
- **Scoring:** [evaluate_loss](../../src/toruk_lm/engine.py) scores each document target once, including EOS; the demo's [measure.py](../../artifacts/minimal-lm-demo-001/measure.py) independently computes teacher-forced top-1 accuracy. Its greedy sample is a separate generation check, not part of teacher-forced loss. The older controlled-world [scorer](../../src/toruk_lm/reproducibility.py) decodes generated IDs, takes the first line, checks labels/IDs, and compares exact answers. Read-only rescoring of saved smoke predictions gives 0/12 for each variant, with 100% attempted-answer coverage.

No out-of-vocabulary ID, off-by-one targets, checkpoint/config mismatch, runaway generation, wrong decoding path, scoring-format mismatch, or actual train/validation file leak was reproduced. No implementation fix was made. The controlled smoke config has only two optimizer steps, two worlds per split, and a two-token answer budget; longer gold values cannot be emitted in full. The older 60-document ordinary fixture is highly templated; its saved 1.2481 nats/byte-or-EOS and repetitive continuations are not a natural-language ability measure. Its checkpoint is unavailable here, so that stored loss was not freshly rescored.

## Measured outcome

The demo's seeded untrained held-out loss was **5.63331 nats/token** and top-1 accuracy **0/136**. Direct fresh scoring of the trained checkpoint gives **0.0915924 nats/token**, **134/136 = 98.53%** top-1 accuracy, and the exact 16-byte greedy continuation `abc abc abc abc `. A constant training-target majority baseline gets 25.74% held-out top-1 accuracy. This exceeds the frozen demo criteria, showing learned prediction of this simple pattern on different-length held-out documents. It does not test vocabulary, syntax, semantics, conversation, or factual recall beyond those four repeated bytes.

## Local checks and commands

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_foundation.py tests/test_worlds.py` — **15 passed** in 47.74 s, including tokenizer, causal/loss, checkpoint reload/resume, generation and CLI evaluation paths.
- Read-only `.\.venv\Scripts\python.exe -` with `load_checkpoint`, `load_model`, `check_separation`, `windows`, `batch`, `evaluate_loss`, `generate`, `sha256_file` on `artifacts/minimal-lm-demo-001/{data,train/checkpoint.pt}` — matching train/validation hashes, step 120, 0.091592396 validation loss, 134/136 top-1, sample above and ID range 1..102. The command's full stdin code was executed in this check and made no writes.
- Read-only `.\.venv\Scripts\python.exe -` with `load_worlds('artifacts/my-smoke/data/validation.jsonl','validation')` and `score_directory(..., budget=2)` on each `ordinary-eval` and `recurrent-eval` directory — **0/12** exact for each, score/label/output consistency checks passed.
- `git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check` — passed for tracked diffs. Untracked files are outside this Git check.

The two read-only Python invocations above were run as PowerShell here-strings piped to `.\.venv\Scripts\python.exe -`. Their exact program bodies were:

```python
# Demo checkpoint rescore
from pathlib import Path
import json, torch
from toruk_lm.data import read_documents, check_separation, windows, batch, sha256_file
from toruk_lm.engine import load_checkpoint, load_model, evaluate_loss, setup
from toruk_lm.model import generate
from toruk_lm.tokenizer import ByteTokenizer
root=Path('artifacts/minimal-lm-demo-001')
train=root/'data/train.jsonl'; val=root/'data/validation.jsonl'; ck=root/'train/checkpoint.pt'
setup(23,1)
check_separation(read_documents(train),read_documents(val))
saved=load_checkpoint(ck); model=load_model(ck)
examples=windows(read_documents(val),model.config.context)
correct=count=0
with torch.no_grad():
    for start in range(0,len(examples),4):
        x,y=batch(examples[start:start+4]); mask=y.ne(-100)
        correct+=int((model(x).argmax(-1)[mask]==y[mask]).sum()); count+=int(mask.sum())
t=ByteTokenizer(); sample=t.decode(generate(model,[t.bos_id,*t.encode('abc ')],16))
print(json.dumps({'checkpoint_sha256':sha256_file(ck),'saved_datasets':saved['datasets'],'actual_datasets':{'train':sha256_file(train),'validation':sha256_file(val)},'next_step':saved['next_step'],'parameters':sum(p.numel() for p in model.parameters()),'validation_loss':evaluate_loss(model,val)['loss_nats_per_byte_or_eos'],'correct':correct,'tokens':count,'sample':sample,'min_id':min(i for xs,ys in examples for i in xs+ys),'max_id':max(i for xs,ys in examples for i in xs+ys)},indent=2))

# Controlled-world saved-output rescore (separate invocation)
from pathlib import Path
from toruk_lm.worlds import load_worlds
from toruk_lm.reproducibility import score_directory
root=Path('artifacts/my-smoke')
rows=load_worlds(root/'data/validation.jsonl','validation')
for variant in ('ordinary','recurrent'):
    result=score_directory(root/f'{variant}-eval',rows,2)
    print(variant,result['examples'],result['exact_accuracy'],result['answer_coverage'])
```

No code changed, so the project verification command was not rerun in this follow-up. In the immediately preceding demo run on this same commit and source state, `scripts/verify.py` passed 86 tests and its non-type checks, but exited nonzero on two mypy checks because NumPy 2.5.4's Python 3.12 `type` syntax conflicts with the project's Python 3.11 mypy target; that is a prior local result, not a pass for this check. GitHub Actions was not run or inspected; no remote status is claimed.

**Single most useful next step:** freeze a bounded held-out corpus with more than one token pattern and report next-token loss, accuracy and generations against a train-only baseline before claiming broader language ability.
