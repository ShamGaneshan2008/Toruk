---
title: Toruk private qualification backend
sdk: docker
app_port: 7860
---

Experimental qualification service. Chat quality unqualified; efficiency claim unsupported.
Backbone: HuggingFaceTB/SmolLM2-135M-Instruct, Apache-2.0, revision
12fd25f77366fa6b3b4b768ec3050bf629380bac. The pretrained backbone supplies language ability.
Toruk uses a separately provisioned, hash-checked M6 selector. No fallback model.
Keep this Space private for initial qualification. Protected visibility is needed for
a reachable authenticated Vercel origin without publishing source/checkpoint files.
See the repository's docs/public-inference-gate.md before any upload.
