"""Sentence Transformers Quickstart Examples (v5.x)."""
from sentence_transformers import SentenceTransformer, CrossEncoder, SparseEncoder
from sentence_transformers.util import cos_sim

# === Dense Embeddings ===
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
texts = ["The weather is lovely.", "It's so sunny outside!", "He drove to the stadium."]
embeddings = model.encode(texts, normalize_embeddings=True)
print(f"Embeddings shape: {embeddings.shape}")  # (3, 384)

sim = cos_sim(embeddings[0], embeddings[1])
print(f"Similarity: {sim.item():.4f}")  # ~0.85

# === Reranker ===
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
pairs = [
    ("What is Python?", "Python is a programming language."),
    ("What is Python?", "Monty Python is a comedy group."),
]
scores = reranker.predict(pairs)
print(f"Reranker scores: {scores}")  # [7.2, 1.8] approx

# === Sparse Embeddings ===
sparse = SparseEncoder("prithivida/Splade_PP_en_v1")
sparse_emb = sparse.encode(texts)
print(f"Sparse embedding type: {type(sparse_emb)}")  # list of dicts
