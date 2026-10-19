import json
import subprocess
import sys

import pytest
import torch

from toruk_lm.data import batch, check_separation, make_fixture, read_documents, windows
from toruk_lm.engine import TrainConfig, evaluate_loss, load_checkpoint, load_model, setup, train
from toruk_lm.model import CausalLM, ModelConfig, generate, loss_sum
from toruk_lm.tokenizer import ByteTokenizer


@pytest.fixture(autouse=True)
def deterministic():
    setup(9, 1)


def tiny():
    return CausalLM(ModelConfig(context=8, width=16, heads=2, layers=1)).eval()


def test_tokenizer_round_trip():
    tokenizer = ByteTokenizer()
    text = "Toruk: café, नमस्ते, 🦉"
    assert tokenizer.decode(tokenizer.encode(text, document=True)) == text


def test_future_tokens_cannot_change_earlier_logits():
    model = tiny()
    original = torch.tensor([[1, 10, 11, 12, 13, 14]])
    changed = original.clone()
    changed[:, 3:] = torch.tensor([90, 91, 92])
    torch.testing.assert_close(model(original)[:, :3], model(changed)[:, :3], rtol=0, atol=0)
    assert not torch.equal(model(original)[:, 3:], model(changed)[:, 3:])


def test_padding_and_batch_isolation():
    model = tiny()
    first = torch.tensor([[1, 10, 11]])
    with torch.no_grad():
        alone = model(first)
        padded = model(torch.tensor([[1, 10, 11, 0, 0], [1, 90, 91, 92, 93]]))
        changed = model(torch.tensor([[1, 10, 11, 0, 0], [1, 40, 41, 42, 43]]))
    torch.testing.assert_close(alone, padded[:1, :3], atol=1e-6, rtol=1e-6)
    torch.testing.assert_close(padded[:1, :3], changed[:1, :3], atol=0, rtol=0)
    with pytest.raises(ValueError, match="fully padded"):
        model(torch.zeros(1, 3, dtype=torch.long))
    with pytest.raises(ValueError, match="right padding"):
        model(torch.tensor([[1, 0, 3]]))


def test_shift_and_boundary_targets_once():
    tokenizer = ByteTokenizer()
    text = "abcdefghijk"
    examples = windows([{"id": "a", "text": text}], context=4)
    tokens = tokenizer.encode(text, document=True)
    assert [t for x, _ in examples for t in x] == tokens[:-1]
    assert [t for _, y in examples for t in y] == tokens[1:]
    assert examples[0][1][-1] == examples[1][0][0]
    assert examples[1][1][0] == tokens[5]
    assert examples[-1][1][-1] == tokenizer.eos_id


def test_valid_token_loss_and_gradients():
    model = tiny()
    x, y = batch([([1, 10, 11], [10, 11, 2]), ([1], [2])])
    summed, count = loss_sum(model(x), y)
    assert count == 4
    individual = sum(loss_sum(model(a[None]), b[None])[0] for a, b in zip(x, y, strict=True))
    torch.testing.assert_close(summed, individual)
    (summed / count).backward()
    for parameter in model.parameters():
        assert parameter.grad is not None
        assert torch.isfinite(parameter.grad).all()
    assert model.blocks[0].attention.in_proj_weight.grad.abs().sum() > 0
    assert model.embedding.weight.grad[0].count_nonzero() == 0


def test_local_window_generation_and_no_hidden_session_state():
    model = tiny()
    suffix = [10, 11, 12, 13, 14, 15, 16, 17]
    assert generate(model, [30, *suffix], 5) == generate(model, [90, *suffix], 5)
    first = generate(model, [1, 42], 5)
    generate(model, [1, 97], 5)
    assert generate(model, [1, 42], 5) == first
    # Each newly generated token becomes causal context for the next prediction.
    history = [1, 42]
    manual = []
    for _ in range(5):
        logits = model(torch.tensor([history[-8:]]))[0, -1].detach().clone()
        logits[:2] = -torch.inf
        token = logits.argmax().item()
        manual.append(token)
        history.append(token)
        if token == 2:
            break
    assert first == manual
    with pytest.raises(ValueError, match="context"):
        model(torch.ones(1, 9, dtype=torch.long))


def test_fixture_determinism_and_document_separation(tmp_path):
    left = make_fixture(tmp_path / "left", documents=20)
    right = make_fixture(tmp_path / "right", documents=20)
    assert left == right
    ids = [set(left["splits"][name]["ids"]) for name in ("train", "validation", "test")]
    assert not (ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])
    a = read_documents(tmp_path / "left/train.jsonl")
    b = read_documents(tmp_path / "left/validation.jsonl")
    check_separation(a, b)
    with pytest.raises(ValueError, match="overlap"):
        check_separation(a, a)
    with pytest.raises(ValueError, match="overwrite"):
        make_fixture(tmp_path / "left")


def test_reload_resume_exact_and_mismatch_rejection(tmp_path):
    make_fixture(tmp_path / "data", documents=10)
    train_path = tmp_path / "data/train.jsonl"
    validation = tmp_path / "data/validation.jsonl"
    model_config = ModelConfig(context=8, width=16, heads=2, layers=1)
    config = TrainConfig(batch_size=2)
    train(train_path, validation, tmp_path / "full", model_config, config, 4)
    train(train_path, validation, tmp_path / "part", model_config, config, 2)
    part = tmp_path / "part/checkpoint.pt"
    train(train_path, validation, tmp_path / "resumed", model_config, config, 4, part)
    full = load_checkpoint(tmp_path / "full/checkpoint.pt")
    resumed = load_checkpoint(tmp_path / "resumed/checkpoint.pt")
    for key in full["model"]:
        torch.testing.assert_close(full["model"][key], resumed["model"][key], rtol=0, atol=0)
    for key in full["optimizer"]["state"]:
        for field in full["optimizer"]["state"][key]:
            torch.testing.assert_close(
                full["optimizer"]["state"][key][field],
                resumed["optimizer"]["state"][key][field],
                rtol=0,
                atol=0,
            )
    torch.testing.assert_close(full["torch_rng"], resumed["torch_rng"], rtol=0, atol=0)
    assert full["python_rng"] == resumed["python_rng"]
    model = load_model(tmp_path / "full/checkpoint.pt")
    reloaded = load_model(tmp_path / "resumed/checkpoint.pt")
    assert generate(model, [1, 40], 5) == generate(reloaded, [1, 40], 5)
    assert (
        evaluate_loss(model, validation)["loss_nats_per_byte_or_eos"]
        == evaluate_loss(
            reloaded,
            validation,
        )["loss_nats_per_byte_or_eos"]
    )
    with pytest.raises(ValueError, match="model_config mismatch"):
        train(train_path, validation, tmp_path / "bad", ModelConfig(), config, 5, part)
    train_path.write_text(train_path.read_text() + '{"id":"extra","text":"extra"}\n')
    with pytest.raises(ValueError, match="datasets mismatch"):
        train(train_path, validation, tmp_path / "changed", model_config, config, 5, part)
    bad = dict(full, format="unsupported-mid-document")
    torch.save(bad, tmp_path / "bad.pt")
    with pytest.raises(ValueError, match="unsupported"):
        load_checkpoint(tmp_path / "bad.pt")


def test_real_cli_pipeline(tmp_path):
    def cli(*args):
        completed = subprocess.run(
            [sys.executable, "-m", "toruk_lm", *map(str, args)],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        return json.loads(completed.stdout)

    data = tmp_path / "data"
    output = tmp_path / "run"
    cli("make-fixture", "--output", data, "--documents", 10)
    fitted = cli(
        "train",
        "--train",
        data / "train.jsonl",
        "--validation",
        data / "validation.jsonl",
        "--output",
        output,
        "--steps",
        2,
        "--context",
        16,
        "--width",
        16,
        "--layers",
        1,
    )
    assert fitted["steps_completed"] == 2
    scored = cli(
        "evaluate",
        "--checkpoint",
        output / "checkpoint.pt",
        "--data",
        data / "validation.jsonl",
        "--output",
        tmp_path / "eval",
        "--max-new-tokens",
        3,
    )
    assert scored["valid_tokens"] > 0
    assert scored["generation"]["generated_tokens"] > 0
    predictions = json.loads((tmp_path / "eval/predictions.json").read_text())
    generated = cli(
        "generate",
        "--checkpoint",
        output / "checkpoint.pt",
        "--prompt",
        predictions[0]["prefix"],
        "--max-new-tokens",
        3,
    )
    assert generated["ids"] == predictions[0]["generated_ids"]
    assert cli("diagnose")["training_device"] == "cpu"
