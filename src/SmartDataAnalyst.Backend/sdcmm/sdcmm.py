from typing import List, Dict, Optional
from .vector_store import VectorStore
from utils.utils import generate_id
from models.history import HistoryQuery, HistorySession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

class SDCM:
    """
    Smart Data Context Manager:
    - Stores semantic memories in ChromaDB
    - Stores history in SQLite
    - Extracts operations/filters
    - Provides context for LLM
    """

    def __init__(self):
        self.vector_store = VectorStore()

    
    #-------------------------------
    # 1. STORE MEMORY IN VECTOR DB
    #-------------------------------
    def add_memory(self, text: str, metadata: dict):
        memory_id = generate_id()
        self.vector_store.add_memory(memory_id, text, metadata)


    #---------------------------------------
    # 2. STORE HISTORY IN SQLITE VIA FASTAPE
    #---------------------------------------
    async def add_history(
        self,
        db: AsyncSession,
        file_name: str,
        question: str,
        answer: str
    ):
        # Fetch or create session
        session_res = await db.execute(
            select(HistorySession).where(HistorySession.file_name == file_name)
        )
        session = session_res.unique().scalars().first()

        if not session:
            session = HistorySession(
                id=generate_id(),
                file_name=file_name,
                upload_date=datetime.utcnow()
            )
            db.add(session)
            await db.flush()

        # Create query
        query_entry = HistoryQuery(
            id=generate_id(),
            session_id=session.id,
            question=question,
            answer=answer,
            timestamp=datetime.now(timezone.utc)
        )

        db.add(query_entry)
        await db.commit()

    #---------------------------------------
    # 3. RETRIEVE CONTEXT (VECTOR SEARCH)
    #---------------------------------------
    def retrieve_similar(self, query: str, top_k: int = 5) -> List[str]:
        results = self.vector_store.search(query, top_k)
        if not results or not results.get("documents"):
            return[]
        return results["documents"][0]
    

    #---------------------------------------------------
    # 4. EXTRACT OPERATIONS + FILTERS (YOUR Requirement)
    #---------------------------------------------------
    def extract_operations_and_filters(self, text: str) -> Dict:
        """
        Very simple heuristic parser.
        You can upgrade this later using LLM if required.
        """
        ops = []
        if "sum" in text.lower(): ops.append("sum")
        if "filter" in text.lower(): ops.append("filter")
        if "average" in text.lower(): ops.append("mean")
        if "groupby" in text.lower(): ops.append("groupby")
        if "aggregate" in text.lower(): ops.append("aggregate")
        if "mean" in text.lower(): ops.append("mean")
        if "sort" in text.lower(): ops.append("sort")
        if "orderby" in text.lower(): ops.append("sort")
        if "sort_values" in text.lower() or "sortvalues" in text.lower() : ops.append("sort")
        if "merge" in text.lower() or "joins" in text.lower(): ops.append("merge") 
        return{
            "operations": ops,
            "filters": text
        }        

    #---------------------------------------------------
    # 5. BUILD CONTEXT FOR analyze_query()
    #---------------------------------------------------
    def build_context_for_llm(self, question: str) -> str:
        """fetch similar memories + summaries."""
        similar = self.retrieve_similar(question, top_k=5)

        context = "\n".join([f"- {item}" for item in similar])

        final = f"""
            User Question: {question}
            Relevant Past Context:
            {context if context else 'No prior context found.'}
        """
        return final
    
    #---------------------------------------------------
    # 6. CLEAR ALL MEMORY (Optional)
    #---------------------------------------------------
    def clear(self):
        self.vector_store.delete_all()

        