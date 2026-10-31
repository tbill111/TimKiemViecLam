"""Embedding văn bản (384 chiều, đã chuẩn hoá L2).

- Mặc định dùng `sentence-transformers` với model đa ngôn ngữ
  `paraphrase-multilingual-MiniLM-L12-v2` (hiểu tiếng Việt lẫn tiếng Anh).
- Khi không cài được `sentence-transformers`/`torch` (ví dụ máy dev Python 3.13), tự lùi về
  `HashingEmbedder`: vector băm n-gram ký tự, tất định, chỉ để chạy test và chạy thử.
  Kết quả của HashingEmbedder KHÔNG dùng để báo cáo chất lượng ngữ nghĩa.

Biến môi trường `EMBEDDER`: `auto` (mặc định) | `st` | `hash`.
"""
from __future__ import annotations

import logging
import os
import re
import unicodedata
import zlib
from typing import Optional, Protocol

import numpy as np

log = logging.getLogger(__name__)

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DIM = 384


class Embedder(Protocol):
    name: str

    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = MODEL_NAME):
        from sentence_transformers import SentenceTransformer  # nạp muộn: gói nặng

        self.name = f"st:{model_name}"
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype=np.float32)


class HashingEmbedder:
    """Băm từ và n-gram ký tự (3-5) vào 384 chiều với dấu ±1, rồi chuẩn hoá L2."""

    name = "hash-384"

    @staticmethod
    def _features(text: str) -> list[str]:
        t = unicodedata.normalize("NFC", text).lower()
        words = re.findall(r"\w+", t)
        feats = [f"w:{w}" for w in words]
        feats += [f"b:{a}_{b}" for a, b in zip(words, words[1:])]
        for w in words:
            padded = f"<{w}>"
            for n in (3, 4, 5):
                feats += [f"c:{padded[i:i + n]}" for i in range(max(0, len(padded) - n + 1))]
        return feats

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), DIM), dtype=np.float32)
        for row, text in enumerate(texts):
            for feat in self._features(text):
                h = zlib.crc32(feat.encode("utf-8"))
                out[row, h % DIM] += 1.0 if (h >> 16) & 1 else -1.0
            norm = np.linalg.norm(out[row])
            if norm > 0:
                out[row] /= norm
        return out


_singleton: Optional[Embedder] = None


def get_embedder() -> Embedder:
    """Trả về embedder dùng chung (nạp một lần)."""
    global _singleton
    if _singleton is not None:
        return _singleton
    mode = os.getenv("EMBEDDER", "auto").lower()
    if mode == "hash":
        _singleton = HashingEmbedder()
    else:
        try:
            _singleton = SentenceTransformerEmbedder()
        except Exception as exc:  # thiếu gói hoặc không tải được model
            if mode == "st":
                raise
            log.warning("Không nạp được sentence-transformers (%s); dùng HashingEmbedder.", exc)
            _singleton = HashingEmbedder()
    return _singleton


def set_embedder(embedder: Optional[Embedder]) -> None:
    """Dùng trong test để ép embedder."""
    global _singleton
    _singleton = embedder


def embed_text(text: str) -> np.ndarray:
    return get_embedder().encode([text])[0]


def to_bytes(vec: np.ndarray) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def from_bytes(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine của hai vector (đã chuẩn hoá thì bằng tích vô hướng)."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))
