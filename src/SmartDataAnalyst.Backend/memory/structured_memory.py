import time
import json
import re
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
from .embedding_service import EmbeddingService
from .memory_store import MemoryStore

def _entry_to_text(entry: Dict[str, Any]) -> str:
    # build a short, information one-line summary 
    # string from a structured entry
    parts = []
    if entry.get("intent"):
        parts.append(f"Intent: {entry['intent']}")
    if entry.get("filters"):
        parts.append(f"filters: {entry['filters']}")    
    if entry.get("operations"):
        parts.append(f"Ops: {', '.join(entry['operations'])}")
    if entry.get("columns_used"):
        parts.append(f"Cols: {', '.join(entry['columns_used'])}")        
    if entry.get("shape"):
        parts.append(f"Shape: {entry['shape'][0]} rows x {entry['shape'][1]} cols")

    header = " | ".join(parts) if parts else "Structured memory entry"

    #include sample rows(small)
    sample = entry.get("sample_rows_text", "")
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry.get("timestamp", time.time())))
    return f"{header}\nTime: {ts}\n{sample}"

# Heuristics to detect operations and filters from code/result text
def _extract_operations_and_filters(text: str) -> Tuple[List[str], str]:
    ops = []
    filters = []

    t = text or ""

    # simple heuristics: detect groupby/aggregate/sort/merge/filter keywords
    if re.search(r"\bgroupby\b", t, flags=re.I):
        ops.append("groupby")
    if re.search(r"\baggregate\b|\bagg\b\bmean\b|\bsum\b|\nreset_index\b", t, flags=re.I):
        ops.append("aggregate")
    if re.search(r"\bsort|order_by|sort_values\b", t, flags=re.I):
        ops.append("sort")
    if re.search(r"\bmerge\b|\bjoins\b", t, flags=re.I):
        ops.append("merge")
    if re.search(r"\bfilter\b|\bwhere\b|\bquery\b|\b==|>=|<=|>|<\b", t, flags=re.I):
        parts = re.split(r"[;\n]", t)
        for p in parts:
            if re.search(r"(==|>=|<=|>|<|!=)",p):
                fp = p.strip()
                if len(fp) < 300:
                    filters.append(fp.replace("\n", " ").strip())

    # compactify
    filters_text = "; ".join(filters) if filters else ""
    return ops, filters_text

class StructuredMemory:
    """
    Structured DataFrame Context memory (SDCM)
    - Keeps structured facts about prior queries and results
    - Stores a short textual summary and an embedding for semantic retrieval
    - Uses a private MemoryStore (FAISS) and EmbeddingService internally
    """

    def __init__(self, dim: int = 384, index_path: Optional[str] = None, embedding_service: Optional[EmbeddingService]=None):
        self.embedding = embedding_service or EmbeddingService()
        self.store = MemoryStore(dim=dim, index_path=index_path or "data/sdc_memory.index")                
        self.entries: list[Dict[str, Any]] = []
        self.index_path = index_path or "data/sdc_memory.index"

    def _make_entry(self, question: str,
                    answer_text: str,
                    sample_rows_text: str = "",
                    sample_rows=None,
                    columns_used: Optional[List[str]] = None,
                    operations: Optional[List[str]] = None,
                    filters: Optional[str] = None,
                    intent: Optional[str] = None) -> Dict[str, Any]:
        ops = operations or []
        cols = columns_used or []
        ops_heur, filters_heur = _extract_operations_and_filters(answer_text)
        # merge heuristics with provided values
        final_ops = sorted(list(set(ops + ops_heur)))
        final_filters = filters or filters_heur or ""
        entry = {
            "question": question,
            "answer_text": answer_text,
            "intent": intent or None,
            "filters": final_filters,
            "operations": final_ops,
            "columns_used": cols,
            "shape": None,
            "sample_rows_text": sample_rows_text,
            "sample_rows": sample_rows,
            "timestamp": time.time(),
        }
        # if sample_rows is a pandas df or has shape, try to set shape
        try:
            if sample_rows is not None:
                entry["shape"] = (int(sample_rows.shape[0]), int(sample_rows.shape[1]))
        except Exception:
            entry["shape"] = None
        return entry
    
    def record(self,
               question: str,
               answer_text: str,
               sample_rows=None,
               columns_used: Optional[List[str]] = None,
               operations: Optional[List[str]] = None,
               filters: Optional[str] = None,
               intent: Optional[str] = None):
        """
        Record a structured memory entry:
        - question, answer_text: strings
        - sample_rows: small pandas DatFrame or list-of-dict (optional)
        - columns_used: optional list of column names
        - operations: optional list like ['groupby', 'sort']
        - filters: optional free-text describing filters
        """

        # produce a sample_rows_text string for prompt-friendly insertion
        sample_rows_text = ""
        sample_rows_serial = None

        try:
            if sample_rows is not None:
                # try pandas DataFrame representation (only keep first N rows/cols)
                try:
                    import pandas as _pd
                    if isinstance(sample_rows, _pd.DataFrame):
                        small = sample_rows.head(5).copy()
                        sample_rows_text = small.tp_csv(index=False, line_terminal= "\n")
                        sample_rows_serial = small.reset_index(drop=True).to_dict(orient="records")
                except Exception:
                    # fallback for list-of-dicts
                    if isinstance(sample_rows, list):
                        sample_rows_serial = sample_rows[:5]
                        sample_rows_text = json.dumps(sample_rows_serial)
        except Exception:
            sample_rows_text = ""

        entry = self._make_entry(
            question=question,
            answer_text=answer_text,
            sample_rows_text=sample_rows_text,
            sample_rows=sample_rows_serial,
            columns_used=columns_used,
            operations=operations,
            filters=filters,
            intent=intent
        )

        # create retrieval text and embedding
        text_blob = _entry_to_text(entry)
        vec = self.embedding.embed_text(text_blob)

        # store in FAISS + parallel entries
        self.store.add_memory(text_blob, vec)
        self.entried.append(entry)

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve top-k structured memory text blobs most
        Returns a concatenated string suitable for prompt insertion.
        """

        try:
            query_vec = self.embedding.embed_text(query)
            results = self.store.retrieve(query_vec, top_k)
            # results are the text blobs; return them joined under a heading
            if not results:
                return ""
            return "\n\n".join([f"[Structured Memory]\n{r}" for r in results])
        except Exception:
            return ""
    
    def save(self, base_path: Optional[str] = None):
        path = base_path or self.index_path

        # save FAISS index and write entries to json
        try:
            self.store.save(path)
        except Exception:
            pass

        try:
            with open(path + ".entries.json", "w", encoding="utf-8") as f:
                json.dump(self.entries, f, default=str, indent=2)
        except Exception:
            pass
    
    def load(self, base_path: Optional[str] = None):
        path = base_path or self.index_path
        try:
            self.store.load(path)
        except Exception:
            pass

        try:
            with open(path + ".entries.json", "w", encoding="utf-8") as f:
                json.dump(self.entries, f, default=str, indent=2)
        except Exception:
            pass

    
    def load(self, base_path: Optional[str] = None):
        path = base_path or self.index_path
        try:
            self.store.load(path)
        except Exception:
            pass
        try:
            with open(path + ".entries.json", "r", encoding="utf-8") as f:
                self.entries = json.load(f)
        except Exception:
            self.entries = []