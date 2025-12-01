import faiss
import numpy as np
import os

class MemoryStore:
    def __init__(self, dim: int, index_path: str = None):
        self.index = faiss.IndexFlatIP(dim) # cosine similarity
        self.vectors = []
        self.texts = []
        self.index_path = index_path

    def save(self, path: str):
        print("memorytore save called")

        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        full_index_path = os.path.abspath(path)
        print("Saving FAISS index to:", full_index_path)
        faiss.write_index(self.index, path)

        txt_path = os.path.abspath(path + ".txt")
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        print("Saving FAISS .txt to:", txt_path)
        
        with open(path + ".txt", "w", encoding="utf-8") as f:
            for t in self.texts:
                f.write(t.replace("\n", " ") + "\n")
        print(f"memory saved in")

    def load(self, path: str):
        if os.path.exists(path):
            self.index = faiss.read_index(path)
        txt_path = path + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                self.texts = [line.strip() for line in f.readlines()]
                
    def add_memory(self, text: str, vector: np.ndarray):
        self.index.add(np.array([vector]).astype('float32'))
        self.texts.append(text)
        self.vectors.append(vector)

    def retrieve(self, query_vector: np.ndarray, top_k: int = 3):
        D, I = self.index.search(np.array([query_vector]).astype('float32'), top_k)
        return [self.texts[i] for i in I[0] if i < len(self.texts)]