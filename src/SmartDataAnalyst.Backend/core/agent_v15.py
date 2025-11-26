from .agent_v14 import Agent_v14
from memory.retriever import ContextRetriever
import io, contextlib, gc, pandas as pd
from .llm_client import ask_llm
import time
import asyncio
import json
import textwrap
#import numpy as np

#soft sandboxed builtins (not secure for untrusted code - replace with subprocess in prod)
_SAFE_BUILTINS = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "list": list,
    "dict": dict,
    "set": set,
    "float": float,
    "int": int,
    "str": str,
    "bool": bool,
    "range": range,
}

class Agent_v15(Agent_v14):
    """
    Agent_v15 enhances Agent_v14 by adding Long-Term Memory (FAISS-based)
    retrieval and persistence. It combines short-term context and long-term 
    knowledge grounding for more intelligent analysis.
    """

    def __init__(self, filename: str, *args, **kwargs):
        super().__init__(filename, *args, **kwargs)
        self.retriever = ContextRetriever() # FAISS + Embeddings setup
        self.faiss_index_path = "data/memory.index"
        self.filename = filename
        # Try loading previously saved FAISS memory if available
        try:
            self.retriever.memory.load(self.faiss_index_path)
        except Exception:
            pass # start fresh if index not found
        self.status = "active"
        self.on_status_change = None
        self.last_activity_time = time.time()
        self._last_context_rows = None  # to store last filtered rows

    # helper to detect references to previous context
    def refers_to_previous_context(self, question: str) -> bool:
        q = question.lower()
        keywords = ["those", "them", "that company", "previous", "previously", 
                    "these", "the above", "the ones", "those rows", "that answer",
                      ]
        return any(k in q for k in keywords)
    
    async def _set_status(self, new_status: str):

        if self.status != new_status and new_status == "idle":
            await asyncio.sleep(2)

        self.status = new_status
        self.last_activity_time = time.time()
        print(f"[Agent_v15] Status changed -> {new_status}")
        if self.on_status_change:   
            try:
                self.on_status_change(self.filename, new_status)
            except Exception as e:
                print(f"[Agent_v15] Status callback error: {e}")
            

    async def analyze_query(self, df: pd.DataFrame, question: str, use_memory: bool = True) -> str:
        """
        Enhanced version of analyze_query:
        - Combines short-term (session) and long-term (FAISS) context.
        - Automatically stores both query and response for future retrieval.
        """                
        await self._set_status("analyzing")
        await asyncio.sleep(2)
        
        preview = df.head(5).to_csv(index=False)

        # --- STEP 1: Collect short-term memory ---
        stm_context = ""
        if use_memory:
            try:
                stm_context = self.get_memory_context(question, char_budget=2000) or ""
            except Exception:
                stm_context = ""

        # --- STEP 2: Retrieve long-term memory ---
        ltm_context = ""
        try:
            ltm_context = self.retriever.retrieve_context(question, top_k=3) or ""
        except Exception:
            pass            

        # --- Decide whether to reuse previews filtered rows ---
        reuse_rows = False
        context_rows_df = None
        if self.refers_to_previous_context(question) and getattr(self, "_last_context_rows", None) is not None:            
            reuse_rows = True
            context_rows_df = self._last_context_rows
        else:
            # We'll attempt to construct a small filtered df sample
            # for LLM to reason on but we keep the full df for code execution
            context_rows_df = None

        # --- STEP 3: Merge context blocks ---
        combined_context = ""
        if stm_context:
            combined_context += f"\n[Short-Term Memory]\n{stm_context}\n"
        if ltm_context:
            combined_context += f"\n[Long-Term Memory]\n{ltm_context}\n"

        prompt = textwrap.dedent(f"""
        You are a careful data analyst assistant. The dataframe is already loaded as `df`.
        Provide only a JSON object (no additional text). The JSON must contain these keys:
        - action: one of ["code","rows","answer"].
        - code: (string) valid Python (pandas) code to run which will compute the answer. 
        If you return code, ensure final answer is saved into a variable named 'result'.
        - rows_filter: (optional) a short pandas-style boolean expression 
        (e.g., "company == 'Company A'") that can be used to filter df.
        - target_columns: a list of column names that the user is asking for.
        - explain: (optional) short explanation (1-2 sentences).
        Rules:
        - If the user asks about a sepcific column, include only that column.
        - If the user asks about multiple attributes, return all relevant columns.
        - If the user asks a broad question (e.g. "show details"), return an empty list.
        - Column names must match the CSV columns exactly.
        - Do not create new column names.
        Example:

        User: "Give me the model name where primary use case is image generation."

        Your output:
        {
        "rows_filter": "Primary Use Case == 'Image Generation'",
        "target_columns": ["Model Name"]
        }

        User: "Which developers created models for image generation?"

        Your output:
        {
        "rows_filter": "Primary Use Case == 'Image Generation'",
        "target_columns": ["Developer"]
        }             

        User: "Show models with parameters above 1 billion."

        Your output:
        {
        "rows_filter": "`Parameters (Billions)` > 1",
        "target_columns": ["Model Name", "Parameters (Billions)"]
        }

        User: "Show all rows where release year is 2022."

        Your output:
        {
        "rows_filter": "`Release Year` == 2022",
        "target_columns": []
        }                    

        If the user question refers to "those/them/previous", resuse the provided
        previously-used rows passed below.
        Do not access external resources. Avoid any filesystem or netwrok operations.
        Dataset sample (first 5 rows):        
        {preview}

        Question: {question}

        Relevant conversation context (if any):
        {combined_context}

        If you return "action": "rows", include rows_filter or a small csv snippet
        in `code` as CSV string.
        Output strictly parseable JSON.
        """)

        # Step 2: Get code from LLM
        try:
            raw_llm = await ask_llm(prompt)
        except Exception as e:
            self._set_status("idle")
            return f"Error calling LLM: {e}"
        
        # First try to extract JSON from raw output
        json_obj = None
        raw = raw_llm.strip()
        try:
            # find the first {...} block
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end != -1 and end > start:
                candidate = raw[start:end]
                json_obj = json.loads(candidate)
        except Exception:
            json_obj = None

        if not json_obj:
            # fallback: assume LLM returned code only - keep old behavior
            try:
                code = self.clean_code_block(raw)
                print("Generated code:\n", code)
                print("df: ", df.head(10))
            except Exception:
                json_obj = None


            # Execute in isolated namespace
            exec_env = {"df": df}
            try:
                # execute with reduced builtins
                exec_globals = {"__builtins__": _SAFE_BUILTINS}
                exec(code, exec_globals, exec_env)
                if "result" in exec_env:
                    result_value = exec_env["result"]
                    result_str = str(result_value)
                else:
                    result_str = "No result variable found."
                # update short + long term memory
                try:
                    self.add_to_memory(question, result_str)
                    self.retriever.add_context(f"Q: {question}\nA: {result_str}")
                except Exception:
                    pass
                await self._set_status("idle")
                self._last_result = result_str
                # store last rows used if the code provided a filtered df snippet
                if "filtered_df" in exec_env and isinstance(exec_env["filtered_df"], pd.DataFrame):
                    self._last_context_rows = exec_env["filtered_df"]
                return result_str
            except Exception as e:
                try:
                    self.add_to_memory(question, f"Error executing code: {e}")
                    self.retriever.add_context(f"Q: {question}\nA: Error {e}")
                except Exception:
                    pass
                await self._set_status("idle")
                return f"Error executing code: {e}"

        # If we have a JSON object from the LLM, handle structured response
        action = json_obj.get("action")
        code = json_obj.get("code", "")
        rows_filter = json_obj.get("rows_filter")
        explain = json_obj.get("explain", "")
        target_columns = json_obj.get("target_columns","")

        print(f"Parsed LLM response JSON: action={action}, rows_filter={rows_filter}, code={code}, explain={explain}")
        # If the LLM suggests a rows_filter and we didn't reuse rows,
        # apply it to build context_rows_df
        if rows_filter and not reuse_rows:
            print("reuse_rows false")
            try:
                # safe eval: use pandas query on df
                context_rows_df = df.query(rows_filter)
                # keep a copy in memory for follow-ups
                self._last_context_rows = context_rows_df.copy()
            except Exception:
                context_rows_df = None        
        
        # If action == "rows", return the preview of context_rows_df
        if action == "rows":
            print("Action is rows")
            if context_rows_df is None:
                print("context_rows_df is None")
                # maybe LLM put CSV in code
                if code:
                    print("actions rows but there is code")
                    # attempt to parse CSV snippet returned in code
                    try:
                        from io import StringIO
                        tmp = pd.read_csv(StringIO(code))
                        self._last_context_rows = tmp
                        preview_rows = tmp.head(50).to_csv(index=False)
                        # persist memory
                        try:
                            self.add_to_memory(question, f"Provided rows preview ({len(tmp)} rows).")
                            self.retriever.add_context(f"Q: {question}\nA: provided rows ({len(tmp)} rows)")
                        except Exception:
                            pass
                        await self._set_status("idle")
                        return preview_rows
                    except Exception as e:
                        await self._set_status("idle")
                        return f"Could not parse rows returned by agent: {e}"
                
                if rows_filter:
                    print("Applying rows filter")
                    try:
                        filter = self.clean_filter(rows_filter)
                        print(f"Filter: {filter}")
                        print(df)
                        filtered_df = df.query(filter)
                        print(filtered_df)

                        if "target_columns" in json_obj and json_obj["target_columns"]:
                            target_cols = json_obj["target_columns"]                            
                            reduced_df = filtered_df[target_cols]
                            return reduced_df.to_markdown(index=False)
                        
                        #rows_text = filtered_df.to_string(index=False)
                        #print(f"rows_text: {rows_text}")
                        #return rows_text
                        return filtered_df.to_markdown(index=False)
                    except Exception as e:
                        return {"error": f"failed to apply rows_filter: {rows_filter}","details": str(e)}
                        
                await self._set_status("idle")
                return "No rows could be generated."
            else:
                print("Returning context_rows_df preview")
                preview_rows = context_rows_df.head(50).to_csv(index=False)
                try:
                    self.add_to_memory(question, f"Provided rows preview ({len(context_rows_df)} rows).")
                    self.retriever.add_context(f"Q: {question}\nA: provided rows ({len(context_rows_df)} rows)")
                except Exception:
                    pass
                await self._set_status("idle")
                return preview_rows
            
        # If action == "code" or "answer", execute code (if provided)
        if action in ("code", "answer"):
            if not code:
                # nothing to run, maybe answer is in explain
                ans = explain or "No code or answer provided."
                try:
                    self.add_to_memory(question, ans)
                    self.retriever.add_context(f"Q: {question}\nA: {ans}")
                except Exception:
                    pass
                await self._set_status("idle")
                return ans
            
            # execute provided code
            exec_env = {"df": df}
            try:
                exec_globals = {"__builtins__": _SAFE_BUILTINS}
                cleaned_code = self.clean_code_block(code)
                # allow the LLM to put `filtered_df = df[...]` so we can store it
                with contextlib.redirect_stdout(io.StringIO()) as _tmp_out:
                    exec(cleaned_code, exec_globals, exec_env)

                if "result" in exec_env:
                    result_value = exec_env["result"]
                    result_str = str(result_value)
                else:
                    # if no result variable, try to capture filtered_df
                    # or printed output
                    if "filtered_df" in exec_env and isinstance(exec_env["filtered_df"], pd.DataFrame):
                        self._last_context_rows = exec_env["filtered_df"].copy()
                        result_str = f"Returned {len(self._last_context_rows)} rows (preview attached)."
                    else:
                        result_str = "Code executed; no `result` variable found."

                # update memories
                try:
                    self.add_to_memory(question, result_str)
                    self.retriever.add_context(f"Q: {question}\nA: {result_str}")
                except Exception:
                    pass           

                await self._set_status("idle")             
                self._last_result = result_str
                return result_str
            except Exception as e:
                try:
                    self.add_to_memory(question,f"Error executing code: {e}")
                    self.retriever.add_context(f"Q: {question}\nA: Error {e}")
                except Exception:
                    pass
                await self._set_status("idle")
                return f"Error executing code: {e}"

        # Fallback
        await self._set_status("idle")
        return "Could not interpret agent response."
    

    def get_status(self):
        # return "active" if self.status else "idle"
        # print(f"{time.time()} - {self.last_activity_time}")
        if time.time() - self.last_activity_time > 120:
            return "idle"
        return self.status
    
    def clean_filter(self, filter:str)-> str:
        import re

        # Remove df[...] wrapper: df['col'] → 'col'
        filter = re.sub(r"df\[(.*?)\]", r"\1", filter)

        # Now f looks like: `'Primary Use Case' == 'Image Generation'`

        # Convert ONLY the left-hand side column name to backticks
        # Pattern: `'something' ==`
        filter = re.sub(r"^'([^']+)'\s*==", r"`\1` == ", filter)

        # Convert remaining column names in df['col'] expressions (if any)
        filter = re.sub(r"'([^']+)'\s*([<>=!]=?)", r"`\1` \2", filter)

        # Make sure the value stays quoted (convert single to double quotes)
        filter = re.sub(r"==\s*'([^']+)'", r'== "\1"', filter)

        return filter
                