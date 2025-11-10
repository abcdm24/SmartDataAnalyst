from .embedding_service import EmbeddingService
from .memory_store import MemoryStore

class ContextRetriever:
    def __init__(self):
        self.embedding = EmbeddingService()
        self.memory = MemoryStore(dim=384) #MiniLM-L6 has 384 dims


    def add_context(self, text: str):
        vec = self.embedding.embed_text(text)
        self.memory.add_memory(text, vec)

    def retrieve_context(self, query: str, top_k: int = 3):
        query_vec = self.embedding.embed_text(query)
        results = self.memory.retrieve(query_vec, top_k)
        return "\n".join(results)

