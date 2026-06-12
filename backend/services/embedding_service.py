import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
except Exception:
    model = None


EMBEDDING_DIM = 384


def get_embedding(text):
    text = str(text or "").strip()

    if not text:
        return [0.0] * EMBEDDING_DIM

    if model is not None:
        return model.encode(text).tolist()

    vector = np.zeros(EMBEDDING_DIM)

    for i, char in enumerate(text):
        vector[i % EMBEDDING_DIM] += ord(char) % 100

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector.tolist()

    return (vector / norm).tolist()


def embedding_similarity(text1, text2):
    text1 = str(text1 or "").strip()
    text2 = str(text2 or "").strip()

    if not text1 or not text2:
        return 0

    emb1 = np.array(get_embedding(text1)).reshape(1, -1)
    emb2 = np.array(get_embedding(text2)).reshape(1, -1)

    score = cosine_similarity(emb1, emb2)[0][0]

    return round(float(score) * 100, 2)