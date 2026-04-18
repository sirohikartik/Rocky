import csv
import json
import numpy as np
import sys
import ast

csv.field_size_limit(sys.maxsize)

def parse_rotations(raw: str):
    if not raw:
        return []

    raw = str(raw).strip()

    try:
        # First pass
        parsed = json.loads(raw)
        
        # If it's STILL a string (the double-encoded issue), parse it again
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
            
        return parsed
    except Exception:
        # Ultimate fallback for weirdly escaped CSV quotes
        try:
            raw_fixed = raw.replace('""', '"')
            parsed = json.loads(raw_fixed)
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
            return parsed
        except Exception as e:
            print(f"❌ JSON PARSE FAIL: {e}")
            return []

def parse_rotations(raw: str):
    if not raw:
        return []

    raw = raw.strip()

    try:
        # DictReader already unescaped the CSV quotes, so we just parse it normally.
        return json.loads(raw)

    except Exception as e:
        print(f"❌ JSON PARSE FAIL: {e}")
        print("RAW:", repr(raw[:200]))
        return []


# ------------------- ENGINE -------------------
class EmbeddingEngine:
    def __init__(self, csv_path):
        self.words = []
        self.embeddings = []
        self.rotations = []
        self.videos = []

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # word
                word = row["word"].strip()
                self.words.append(word)

                # embedding
                try:
                    emb = np.array(json.loads(row["vector_embedding"]), dtype=np.float32)
                except Exception as e:
                    print(f"❌ Embedding parse failed for {word}")
                    emb = np.zeros(384, dtype=np.float32)  # fallback

                self.embeddings.append(emb)

                # rotations
                rotations = parse_rotations(row.get("rotations", ""))

                if len(rotations) == 0:
                     print("❌ EMPTY ROTATION FOR:", word)
                else:
                     print("✅ ROTATION LOADED:", word, "frames:", len(rotations))

                self.rotations.append(rotations)

                self.videos.append(None)

        # stack embeddings
        self.embeddings = np.vstack(self.embeddings)

        # normalize
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / norms

        # lookup map
        self.word_to_index = {w.lower(): i for i, w in enumerate(self.words)}

        # 🔍 DEBUG (prints once)
        print("=== ENGINE LOADED ===")
        print("Total words:", len(self.words))
        print("Sample word:", self.words[0])
        print("Sample rotation length:", len(self.rotations[0]))
        print("=====================")

    # ------------------- SIMILARITY -------------------
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
                "rotations": self.rotations[i],
                "score": float(sims[i])
            })

        return results

    # ------------------- LOOKUP -------------------
    def lookup(self, word: str):
        idx = self.word_to_index.get(word.lower())
        if idx is None:
            return None

        return {
            "word": self.words[idx],
            "rotations": self.rotations[idx]
        }


# ------------------- OPTIONAL MODEL -------------------
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, text: str):
        return self.model.encode(text)
