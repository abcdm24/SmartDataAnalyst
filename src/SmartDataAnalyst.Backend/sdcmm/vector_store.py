import chromadb
from chromadb.config import Settings

class VectorStore:
    """Handles vector storage using ChromaDB."""

    def __init__(self):
        # persists in ./chroma_data folder
        self.client = chromadb.Client(
            Settings
                (is_persistent=True, persist_directory="./chroma_data"))

        self.collection = self.client.get_or_create_collection(
            name="sdcmm_memory",
            metadata={"hnsw:space":"cosine"}
        )

    def add_memory(self, memory_id: str, text: str, metadata: dict):
        self.collection.add(
            ids=[memory_id],
            documents=[text],
            metadata=[metadata]
        )

    def search(self, query: str, top_k: int = 5):
        return self.collection.query(query_texts=[query], n_results=top_k)
    
    def delete_all(self):
        self.client.delete_collection("sdcmm_memory")
        self.collection = self.client.get_or_create_collection("sdcmm_memory")

            