import numpy as np

from app.ai.embedder import DIM, HashingEmbedder, cosine, from_bytes, to_bytes


def test_hash_embedder_shape_norm_and_determinism():
    e = HashingEmbedder()
    a = e.encode(["React và TypeScript"])
    b = e.encode(["React và TypeScript"])
    assert a.shape == (1, DIM)
    assert np.allclose(a, b)
    assert abs(np.linalg.norm(a[0]) - 1.0) < 1e-5


def test_similar_texts_closer_than_unrelated():
    e = HashingEmbedder()
    v = e.encode(["lập trình frontend react", "frontend react developer", "kế toán thuế doanh nghiệp"])
    assert cosine(v[0], v[1]) > cosine(v[0], v[2])


def test_bytes_roundtrip():
    e = HashingEmbedder()
    v = e.encode(["xin chào"])[0]
    assert np.allclose(from_bytes(to_bytes(v)), v)


def test_empty_text_is_zero_vector_and_cosine_safe():
    e = HashingEmbedder()
    v = e.encode([""])[0]
    assert cosine(v, v) == 0.0
