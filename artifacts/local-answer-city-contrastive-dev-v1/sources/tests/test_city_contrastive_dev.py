"""Disposable numerical contracts; no study examples, optimization or generation."""

import copy

import audit_city_contrastive_dev as independent
import city_contrastive_dev as study
import pytest
import torch


def labels():
    return [
        dict(id=f"v2-train-{i:03}", category="city", gold=g, canonical=["bek", "city", g, "city"])
        for i, g in enumerate(("la", "mi"))
    ]


def test_confuser_uses_training_only_and_rejects_ambiguous_inputs():
    data = labels()
    before = copy.deepcopy(data)
    assert study.confuser_map(data) == {"v2-train-000": ord("m") + 3, "v2-train-001": ord("l") + 3}
    assert data == before
    for rows in ([dict(data[0], id="v2-dev-000")], [data[0]]):
        with pytest.raises(ValueError):
            study.confuser_map(rows)


@pytest.mark.parametrize("arm", ["control", "contrast"])
def test_objective_matches_explicit_formula_and_gradients(monkeypatch, arm):
    docs = [
        dict(id="v2-train-000", prefix="x?=", text="x?=la"),
        dict(id="dummy-code", prefix="y?=", text="y?=R-7"),
    ]
    torch.manual_seed(927117)
    logits = torch.randn(2, 64, 259, requires_grad=True)
    calls = []

    def forward(_model, x):
        calls.append(x.shape)
        return logits

    monkeypatch.setattr(study, "forward_batch", forward)
    value, stats = study.objective(
        None, docs, 15, arm=arm, confusers={"v2-train-000": ord("m") + 3}
    )
    x, y, a, f = study.v2.batch_tensors(docs)
    ce, _ = study.v2.loss_from_logits(logits, y, a, f, 15)
    auxiliary = torch.nn.functional.softplus(
        2 + logits[0, 3, ord("m") + 3] - logits[0, 3, ord("l") + 3]
    )
    expected = ce + 0.1 * auxiliary if arm == "contrast" else ce
    assert len(calls) == 1 and stats["city_contributions"] == 1
    torch.testing.assert_close(value, expected, rtol=0, atol=0)
    left = torch.autograd.grad(value, logits, retain_graph=True)[0]
    right = torch.autograd.grad(expected, logits)[0]
    assert torch.equal(left, right)
    assert stats["forward_positions"] == x.numel() == 128
    r = stats["city_records"][0]
    assert independent.softplus(2 + r["confuser_logit"] - r["gold_logit"]) == pytest.approx(
        stats["city_loss"], abs=1e-6
    )


def test_no_city_batch_has_zero_loss_and_no_logit_changes():
    logits = torch.randn(1, 6, 259, requires_grad=True)
    before = logits.detach().clone()
    zero, records = study.contrastive_loss(
        logits,
        torch.ones(1, 6, dtype=torch.long),
        torch.zeros(1, 6, dtype=torch.bool),
        [dict(id="code")],
        {},
    )
    assert zero.item() == 0 and records == [] and torch.equal(before, logits)


def metric(correct):
    return dict(
        exact=sum(correct),
        eos=24,
        categories=dict(city=8, code=8, unknown=8),
        cases=[dict(id=str(i), exact=v) for i, v in enumerate(correct)],
    )


def test_casewise_gate_rejects_hidden_regressions_and_allows_only_ceiling_ties():
    perfect = metric([True] * 24)
    weak = metric([False, False] + [True] * 22)
    fixed = metric([True, False] + [True] * 22)
    swap = metric([True, True, False] + [True] * 21)
    for control, candidate, expected in (
        (perfect, perfect, True),
        (weak, weak, False),
        (weak, fixed, True),
        (weak, swap, False),
    ):
        assert study.pair_gate(control, candidate)["pass_pair"] is expected
        assert independent.pair(control, candidate) == study.pair_gate(control, candidate)


def test_fixed_order_independent_axes_and_caps():
    assert len(set(study.ORDER)) == len(study.ORDER) == 16
    assert study.CAPS["fit"] == 90 and study.CAPS["overall"] == 1800
    assert {study.v2.CROSSED[s]["initialization"] for s, _, _ in study.ORDER} == {601, 947}
    assert {study.v2.CROSSED[s]["shuffle"] for s, _, _ in study.ORDER} == {1301, 1709}


def test_training_loader_rejects_dev_before_plan_access(monkeypatch):
    def forbidden():
        pytest.fail("development request reached file access")

    monkeypatch.setattr(study, "check_plan", forbidden)
    with pytest.raises(ValueError, match="training"):
        study.checked_data("dev-inputs.json", training=True)


def test_adapter_restores_original_paths_on_failure(monkeypatch):
    old = study.v2.RUN, study.v2.EXEC, study.v2.objective
    monkeypatch.setattr(study, "read", lambda _path: {})
    with pytest.raises(RuntimeError), study.adapter("contrast"):
        assert study.v2.RUN == study.RUN
        raise RuntimeError("injected")
    assert (study.v2.RUN, study.v2.EXEC, study.v2.objective) == old


def test_candidate_development_is_blocked_before_model_loading(monkeypatch, tmp_path):
    monkeypatch.setattr(study, "read", lambda _path: {"pass_gate": False})
    with pytest.raises(ValueError, match="control dev barrier"):
        study.evaluate(tmp_path, "i601-s1301", "ordinary", "contrast", "dev")


def test_independent_softplus_is_stable_at_extreme_margins():
    assert independent.softplus(-1000) == 0
    assert independent.softplus(1000) == 1000
    assert independent.softplus(0) == pytest.approx(0.6931471805599453)
