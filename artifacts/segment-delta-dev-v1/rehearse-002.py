"""Disposable random-tensor numeric rehearsal. No optimizer step or generated answer."""

import sys
import time
from pathlib import Path

started = time.perf_counter()
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import torch
from torch import nn
from torch.nn import functional as F

from segment_delta_watch import worker_receipt, write
from toruk_lm.engine import setup
from toruk_lm.model import CausalLM, ModelConfig
from toruk_lm.owned_lm import OwnedConfig, build_model

setup(900733, 1)
ordinary = build_model(OwnedConfig(context=24, width=16, heads=4, layers=1), "ordinary_matched")
recurrent = build_model(OwnedConfig(context=24, width=16, heads=4, layers=1), "memory_on")
base = CausalLM(ModelConfig(context=24, width=16, heads=4, layers=1))
base.blocks[0].ff = nn.Sequential(nn.Linear(16, 116), nn.GELU(), nn.Linear(116, 16))
q, out = nn.Linear(16, 8, bias=False), nn.Linear(8, 16, bias=False)
norm, k, v, beta = nn.LayerNorm(16), nn.Linear(16, 8), nn.Linear(16, 8), nn.Linear(16, 1)
setup_wall = time.perf_counter() - started
costs = []
for repeat in range(3):
    tick, cpu = time.perf_counter(), time.process_time()
    state = torch.zeros(2, 8, 8)
    losses = []
    for segment in range(8):
        tokens = torch.randint(3, 259, (2, 24))
        x = base.embedding(tokens) + base.position(torch.arange(24))
        x = base.blocks[0](x, torch.ones(24, 24, dtype=torch.bool).triu(1), tokens.eq(0))
        query = F.normalize(q(norm(x)), dim=-1, eps=1e-6)
        hidden = base.norm(x + out(torch.bmm(query, state)))
        logits = base.output(hidden)
        losses.append(F.cross_entropy(logits.flatten(0, 1), torch.randint(3, 259, (48,))))
        keys, values, strengths = F.normalize(k(hidden), dim=-1, eps=1e-6), v(hidden).tanh(), beta(hidden).sigmoid()
        for t in range(24):
            error = values[:, t] - torch.bmm(keys[:, t, None], state).squeeze(1)
            state = state + strengths[:, t, :, None] * keys[:, t, :, None] * error[:, None]
    torch.stack(losses).mean().backward()
    for module in (base, q, out, norm, k, v, beta):
        module.zero_grad(set_to_none=True)
    costs.append(dict(wall=time.perf_counter()-tick, cpu=time.process_time()-cpu))
count = sum(p.numel() for module in (base, q, out, norm, k, v, beta) for p in module.parameters())
write(Path(__file__).with_name("rehearsal-002-numeric.json"), dict(
    seed=900733, random_only=True, document_positions=192, batch=2, backward_repeats=3,
    optimizer_steps=0, generated_answers=0, cold_setup_wall=setup_wall, repetitions=costs,
    parameters=dict(ordinary=sum(p.numel() for p in ordinary.parameters()), recurrent=sum(p.numel() for p in recurrent.parameters()), delta=count),
    state_bytes=256,
))
worker_receipt(Path(__file__).with_name("rehearsal-002"), started, setup_wall)

