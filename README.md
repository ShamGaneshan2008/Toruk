<div align="center">
  <h1>TORUK</h1>
  <p><strong>Remember what matters. Revise what changed.</strong></p>
  <p>An experimental language model exploring useful memory under fixed resource limits.</p>
  <p><img src="https://img.shields.io/badge/status-research-41627A" alt="Status: research" /></p>
</div>

[Research focus](#research-focus) · [Development status](#development-status) · [Getting started](#getting-started) · [Roadmap](#roadmap)

## Overview

Toruk investigates how a language model can carry useful information through a long stream while operating with bounded internal memory. The model family is **Toruk-LM**; its Python package is **`toruk_lm`**. The central question is whether a model can retain relevant context, incorporate corrections, and preserve facts that remain valid without letting its memory grow with every new piece of text.

The current repository provides a compact causal language model as a research foundation. Bounded learned memory and the experiments needed to assess it are still planned.

## Why this matters

Long histories contain both useful facts and distractions. Some facts later change; others must survive those changes. A fixed memory budget makes every update a choice: what should remain available, what should be revised, and what must not be disturbed?

Toruk studies those choices through controlled comparisons with simpler language models, alongside measurements of the resources each approach uses.

## Research focus

| Area | Research question | Intended assessment |
| --- | --- | --- |
| Retention | Can earlier information remain useful after it leaves the local text window? | Delayed-recall tasks at increasing distances from the evidence. |
| Revision | Can later corrections replace outdated information? | Accuracy on corrected facts. |
| Preservation | Can a correction leave unrelated valid facts intact? | Accuracy on unchanged facts after a correction. |
| Resource efficiency | What does improved recall cost under a fixed memory budget? | State size, throughput, and total history-to-answer latency. |

**Illustrative research objective.** A record says *Mira lives in Pune and works as a botanist*. Later, it says *Mira moved to Jaipur*. A successful response would use **Jaipur** for her city while retaining **botanist** as her occupation. This is an example of the behavior Toruk aims to study, not a model result.

## What Toruk investigates

The project explores memory within the model's computation, with explicit capacity limits. It tests recall alongside correction and preservation, then compares any gains with simpler alternatives under the same evaluation rules. Selective memory management is a research direction, not an established capability of the current model.

## Development status

| Component | Status | Evidence or next step |
| --- | --- | --- |
| Ordinary causal LM | **Verified** | Local tests cover causality, training, checkpoint reload and resume, and generation. |
| Document-separated text fixture | **Verified** | A saved CPU pilot covers ordinary-text loss and generated continuations; it does not measure factual recall. |
| Controlled factual benchmark and independent scoring | **Planned** | Needed before a meaningful memory comparison. |
| Bounded learned memory | **Planned** | Design work exists; no memory model has been trained or evaluated. |
| Correction, preservation, and resource comparisons | **Planned** | No supported accuracy or efficiency claim yet. |

The [pilot metrics](artifacts/foundation-001/eval/metrics.json) report validation text loss and continuation timing for the ordinary model. The run used a small, repetitive fixture; its generated text was repetitive too. These results verify the pipeline, not the research objective above.

## Getting started

Python 3.11 or later is required. From a Python environment in this repository, install the CPU PyTorch build and the package, then inspect the available commands:

```sh
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e .
python -m toruk_lm --help
python -m toruk_lm diagnose
```

The CLI currently supports fixture generation, ordinary-LM training, evaluation, and text generation. It does not offer a recurrent-memory model. The package also installs the `toruk` command.

## Evaluation principles

Language quality and factual answers require different measurements. Toruk aims to report ordinary-text loss separately from answers generated without seeing reference answers. Future controlled evaluations should cover delayed recall, corrections, unchanged facts, unknown answers, and behavior as memory fills.

Resource comparisons must include the full history read, memory operations, and answer time. A small stored state does not mean the model read fewer input tokens, and no unlimited-context or speedup claim follows from the current pilot.

## Roadmap

1. **Foundation:** establish a causal LM and reproducible local pipeline. The ordinary-LM foundation is verified locally.
2. **Memory experiments:** implement and test bounded learned memory.
3. **Controlled comparisons:** evaluate recall, revision, preservation, and resource cost against simpler baselines.
4. **Reproducibility and technical release:** share methods and results when the experiments support them.

## Research status and disclosure

Toruk is under active research. This page describes its goals and public development progress. Repository files already include code, design notes, and pilot artifacts; a formal technical release has not been issued. No publication date is announced.

## Attribution and license

Toruk builds on established causal language modeling and memory research. Ordinary recurrent memory and gating are not claimed as new inventions here. The current implementation uses [PyTorch](https://pytorch.org/). No project license has been specified, and there is no paper or citation to provide yet.
