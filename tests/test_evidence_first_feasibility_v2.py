"""New disposable source-linked examples, independent of the four old outputs."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evidence_first_feasibility_v2 as stress  # noqa: E402
from evidence_first_policy import (  # noqa: E402
    AMBIGUOUS,
    SUPPORTED,
    answer,
    make_view,
    reslice,
)


def disposable_view():
    messages = [
        {"role": "user", "content": 'OpalRelay\'s flux is " 0.84 tesla ".'},
        {"role": "user", "content": 'JadeRotor\'s offset is "−3.6 mm".'},
        {"role": "user", "content": "Combine OpalRelay's flux and JadeRotor's offset."},
    ]
    return make_view(messages, [0, 1, 2], [0, 1, 2])


@pytest.mark.parametrize("separator", ["; ", " and ", ", ", "\n"])
def test_disposable_valid_two_premise_synthesis_preserves_both_byte_spans(separator):
    view = disposable_view()
    generated = separator.join((" 0.84 tesla ", "−3.6 mm"))
    calls = []

    def decoder():
        calls.append(1)
        return generated

    result = answer(view, token_count=lambda text: len(text.encode()), generate=decoder)
    assert result.state == SUPPORTED and result.route == "synthesis"
    assert result.payload.encode() == generated.encode()
    assert calls == [1] and len(result.sources) == 2
    assert tuple(reslice(view, p).encode() for p in result.sources) == (
        b" 0.84 tesla ",
        "−3.6 mm".encode(),
    )
    assert tuple(p.turn for p in result.sources) == ("m0", "m1")
    assert all(p.revision == view.manifest.revision for p in result.sources)
    assert result.coverage.complete


@pytest.mark.parametrize(
    "generated",
    [
        " 0.84 tesla  and −3.6 mm; both devices are certified safe",
        "−3.6 mm",  # One correct premise is insufficient for a two-premise request.
        " 0.84 tesla ",
        " 0.84 tesla  and 8.1 mm",
        "−3.6 mm and  0.84 tesla ",
    ],
)
def test_disposable_unsupported_claim_or_missing_premise_is_never_published(generated):
    view = disposable_view()
    result = answer(view, token_count=lambda text: len(text.encode()), generate=lambda: generated)
    assert result.state == AMBIGUOUS and result.route == "abstain"
    assert result.payload == "UNKNOWN" and result.reason == "unsupported synthesis output"
    assert result.generated == generated and len(result.sources) == 2
    assert tuple(reslice(view, p) for p in result.sources) == (" 0.84 tesla ", "−3.6 mm")


def test_stress_decoder_changes_only_termination_without_forcing_answer_tokens():
    import torch

    calls = []

    class Tokenizer:
        eos_token_id = 9
        pad_token_id = 0

        def decode(self, ids, skip_special_tokens):
            assert ids == [42] * 64 and skip_special_tokens
            return "synthetic output"

    class Model:
        def generate(self, **kwargs):
            calls.append(kwargs)
            return torch.tensor([[1, 2, 3] + [42] * 64])

    class Backend:
        model = Model()
        tokenizer = Tokenizer()
        model_id = "fake-no-model-loaded"

    tokens = torch.tensor([[1, 2, 3]])
    generated, text = stress.StressDecoder(Backend()).generate_once(tokens)
    assert len(generated) == 64 and text == "synthetic output" and len(calls) == 1
    assert calls[0]["min_new_tokens"] == calls[0]["max_new_tokens"] == 64
    assert calls[0]["input_ids"] is tokens
    assert "forced_decoder_ids" not in calls[0] and "logits_processor" not in calls[0]


@pytest.mark.parametrize("old_request,expected", [(3, 40), (50, 100)])
def test_cap_rule_uses_pooled_maxima_and_all_49_requests(
    tmp_path, monkeypatch, old_request, expected
):
    old = tmp_path / "old"
    rows = old / "pass-1" / "T-P"
    rows.mkdir(parents=True)
    (old / "summary.json").write_text(
        json.dumps(
            {
                "proposed_caps": {
                    "max_nonrequest_wall_seconds": 9,
                    "max_nonrequest_cpu_seconds": 18,
                    "shared_wall_seconds": 127,
                    "shared_cpu_seconds": 94,
                }
            }
        )
    )
    (rows / "requests.jsonl").write_text(
        json.dumps(
            {
                "cost": {
                    "request_wall_seconds": old_request,
                    "request_cpu_seconds": 6,
                }
            }
        )
        + "\n"
    )
    monkeypatch.setattr(stress, "OLD", old)
    data = [
        {"cell": cell, "pass": n, "cost": {"request_wall_seconds": 20, "request_cpu_seconds": 40}}
        for n in (1, 2)
        for cell in ("T", "L")
        for _ in range(3)
    ]
    stages = [
        {"cell": cell, "pass": n, "wall_seconds": 70, "cpu_seconds": 140}
        for n in (1, 2)
        for cell in ("T", "L")
    ]
    caps = stress.propose_caps(data, stages, 2, 3)
    assert caps["request_wall_seconds"] == expected
    assert caps["request_cpu_seconds"] == 80
    assert caps["cell_pass_wall_seconds"] == 20 + 49 * expected
    assert caps["cell_pass_cpu_seconds"] == 40 + 49 * 80
    assert caps["overall_wall_seconds"] == 8 * (20 + 49 * expected) + 127
    assert caps["overall_cpu_seconds"] == 8 * (40 + 49 * 80) + 144


@pytest.mark.parametrize("mutation", ["extra", "gold", "duplicate", "not-disposable"])
def test_stress_registration_cannot_accept_48_case_data_or_oracles(mutation):
    cases = [
        {"id": "new-a", "disposable": True, "messages": [{}] * 32},
        {"id": "new-b", "disposable": True, "messages": [{}] * 48},
    ]
    if mutation == "extra":
        cases.append(dict(cases[0]))
    elif mutation == "gold":
        cases[0]["expected"] = "not permitted"
    elif mutation == "duplicate":
        cases[1]["id"] = cases[0]["id"]
    else:
        cases[0]["disposable"] = False
    with pytest.raises(ValueError):
        stress.validate_cases(cases)
