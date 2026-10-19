"""Fixed UTF-8 byte tokenizer; no vocabulary fitting or split contamination."""

import hashlib


class ByteTokenizer:
    pad_id = 0
    bos_id = 1
    eos_id = 2
    vocab_size = 259
    identity = "toruk-utf8-byte-v1"
    fingerprint = hashlib.sha256(b"toruk-utf8-byte-v1:pad=0,bos=1,eos=2,byte+3").hexdigest()

    def encode(self, text: str, *, document: bool = False) -> list[int]:
        tokens = [byte + 3 for byte in text.encode("utf-8")]
        return [self.bos_id, *tokens, self.eos_id] if document else tokens

    def decode(self, tokens: list[int]) -> str:
        return bytes(token - 3 for token in tokens if 3 <= token < 259).decode(
            "utf-8", errors="replace"
        )
