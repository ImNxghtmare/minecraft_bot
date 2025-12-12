import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticSearch:
    def __init__(self):
        # Лёгкая, быстрая, лучшая мультиязычная модель
        self.model = SentenceTransformer("intfloat/multilingual-e5-base")
        self.index = faiss.IndexFlatL2(768)  # размер вектора модели
        self.text_chunks = []

    def embed(self, text: str):
        emb = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
        return emb

    def add_documents(self, docs: list[str]):
        self.text_chunks.extend(docs)
        vecs = self.model.encode(docs, convert_to_numpy=True, normalize_embeddings=True)
        self.index.add(vecs)

    def search(self, query: str, top_k=3):
        q = self.embed(query)
        distances, ids = self.index.search(q, top_k)

        results = []
        for idx, score in zip(ids[0], distances[0]):
            if idx < len(self.text_chunks):
                results.append((self.text_chunks[idx], float(score)))

        return results
