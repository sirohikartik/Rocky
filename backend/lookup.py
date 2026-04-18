import csv
import json
import numpy as np

class EmbeddingEngine:
    def __init__(self, csv_path):
        self.words = []
        self.embeddings = []
        self.videos = []

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # clean word like "1. loud" -> "loud"
                word = row["word"].split(".")[-1].strip()
                self.words.append(word)

                emb = np.array(json.loads(row["vector_embedding"]), dtype=np.float32)
                self.embeddings.append(emb)

                # no video column yet
                self.videos.append(None)

        self.embeddings = np.vstack(self.embeddings)

        # normalize embeddings once (faster similarity)
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / norms

        # fast lookup map
        self.word_to_index = {w.lower(): i for i, w in enumerate(self.words)}

    def _cosine_similarity(self, vec):
        vec = vec / np.linalg.norm(vec)
        return self.embeddings @ vec

    def find_similar(self, query_embedding, top_k=3):
        query_embedding = np.array(query_embedding, dtype=np.float32)

        sims = self._cosine_similarity(query_embedding)
        idxs = np.argsort(-sims)[:top_k]

        results = []
        for i in idxs:
            results.append({
                "word": self.words[i],
                "video": self.videos[i],
                "score": float(sims[i])
            })

        return results

    def lookup(self, word: str):
        idx = self.word_to_index.get(word.lower())
        if idx is None:
            return None

        return {
            "word": self.words[idx],
            "video": self.videos[idx]
        }


# ------------------- OPTIONAL: embedding model -------------------

from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, text: str):
        return self.model.encode(text)


# ------------------- USAGE -------------------

if __name__ == "__main__":
    engine = EmbeddingEngine("isl_word_embeddings.csv")
    model = EmbeddingModel()

    # direct lookup
    print(engine.lookup("loud"))

    # similarity search
    query_vec = model.encode("noisy")
    print(engine.find_similar(query_vec))


def test_engine():
    print("=== LOADING ENGINE ===")
    engine = EmbeddingEngine("isl_word_embeddings.csv")
    model = EmbeddingModel()

    print("\n=== DIRECT LOOKUP TESTS ===")

    test_words = ["loud", "mean", "rich", "poor", "thick", "LOUD"]

    for w in test_words:
        result = engine.lookup(w)
        print(f"lookup('{w}') -> {result}")

    print("\n=== SIMILARITY TESTS ===")

    query_words = ["noisy", "wealthy", "thin", "kind"]

    for q in query_words:
        print(f"\nQuery: '{q}'")
        vec = model.encode(q)
        results = engine.find_similar(vec, top_k=3)

        for r in results:
            print(f"  -> {r['word']} (score={r['score']:.4f})")

    print("\n=== EDGE CASE TESTS ===")

    # word not in CSV
    missing = "banana"
    print(f"lookup('{missing}') -> {engine.lookup(missing)}")

    # empty / weird input
    weird = ""
    print(f"lookup('{weird}') -> {engine.lookup(weird)}")


if __name__ == "__main__":
    test_engine()
