# agents/agent_v16.py
from .agent_v13 import Agent_v13
import time
import asyncio
import json
import re
import io
import contextlib
from string import Template
import textwrap

import pandas as pd
from typing import Dict, Any, Tuple
from .llm_client import ask_llm           # existing LLM wrapper
from utils.json_repair import repair_json  # your repair helper
from sdcmm.sdcmm import SDCM              # new SDCM module (ChromaDB + SQLite)
from utils.normalizer import normalize_dataframe


# safe builtin subset for exec
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

class Agent_v16(Agent_v13):
    """
    Agent_v16 — extends Agent_v13 to reuse short-term memory helpers while
    integrating the new SDCM (ChromaDB + SQLite) for long-term semantic memory.

    Preserves:
      - status tracking and callbacks from Agent_v13
      - sandboxed code execution pattern
      - same LLM prompt + JSON action flow (action/code/rows/target_columns)
    """

    def __init__(self, filename: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.sdcm = SDCM()  # new SDCM instance (ChromaDB + SQLite)
        # Keep last rows / last result semantics
        self._last_context_rows = None
        self._last_result = None

        # status tracking
        self.status = "active"
        self.on_status_change = None
        self.last_activity_time = time.time()

    # -------------------------
    # Status helpers (unchanged)
    # -------------------------
    async def _set_status(self, new_status: str):
        if self.status != new_status and new_status == "idle":
            # keep previous behaviour (small delay before idle)
            await asyncio.sleep(2)
        self.status = new_status
        self.last_activity_time = time.time()
        print(f"[Agent_v16] Status changed -> {new_status}")
        if self.on_status_change:
            try:
                self.on_status_change(self.filename, new_status)
            except Exception as e:
                print(f"[Agent_v16] Status callback error: {e}")

    def get_status(self):
        print(f"Get Status: {self.status}")
        if time.time() - self.last_activity_time > 120:
            return "idle"
        return self.status

    # -------------------------
    # Small helpers (local)
    # -------------------------
    def refers_to_previous_context(self, question: str) -> bool:
        q = (question or "").lower()
        keywords = ["those", "them", "that company", "previous", "previously",
                    "these", "the above", "the ones", "those rows", "that answer"]
        return any(k in q for k in keywords)

    def clean_filter(self, filter: str) -> str:
        # reuse your original implementation (keeps behaviour)
        import re
        filt = filter
        filt = re.sub(r"df\[(.*?)\]", r"\1", filt)
        filt = re.sub(r"^'([^']+)'\s*==", r"`\1` == ", filt)
        filt = re.sub(r"'([^']+)'\s*([<>=!]=?)", r"`\1` \2", filt)
        filt = re.sub(r"==\s*'([^']+)'", r'== "\1"', filt)
        return filt

    def clean_code_block(self, code: str) -> str:
        """
        Very small sanitizer: remove leading/trailing backticks and ``` markers.
        You can extend this if you have a more advanced version in your repo.
        """
        if not code:
            return ""
        s = code.strip()
        # remove fenced code blocks
        if s.startswith("```") and s.endswith("```"):
            # remove first and last fence (and optional "python")
            lines = s.splitlines()
            # drop fences
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            s = "\n".join(lines)
        # remove single backticks wrapping
        if s.startswith("`") and s.endswith("`"):
            s = s[1:-1]
        return s

    def strip_imports(self, code: str) -> str:
        """Prevent `import` statements (sandbox can't call __import__)."""
        if not code:
            return ""
        lines = code.splitlines()
        cleaned = [ln for ln in lines if not ln.strip().startswith("import")]
        return "\n".join(cleaned)

    def prepare_code(self, code: str) -> str:
        """
        Minimal prepare_code: strip imports and return cleaned code.
        You might already have a more advanced version; this one is safe.
        """
        code = self.clean_code_block(code)
        code = self.strip_imports(code)
        return code

    # -------------------------
    # analyze_query: main flow (keeps JSON/action logic)
    # -------------------------
    async def analyze_query(self, df: pd.DataFrame, question: str, use_memory: bool = True) -> str:
        """
        Entry point similar to v15: same prompt and JSON 'action' flow retained.
        Integrates SDCM for semantic memory (retrieve & store).
        """

        await self._set_status("analyzing")
        # slight delay to keep parity with v15 behaviour
        await asyncio.sleep(2)

        # automatic cleaning
        df = normalize_dataframe(df)

        preview = df.head(5).to_csv(index=False)

        # --- STEP 1: Collect short-term memory (use existing get_memory_context if present)
        combined_context, reuse_rows = await self.get_context(use_memory,question)

        # keep original large prompt text and JSON rules (unchanged)
        prompt = await self.prepare_prompt(preview, question, combined_context)

        # Step: Call LLM
        try:
            raw_llm = await ask_llm(prompt)
        except Exception as e:
            await self._set_status("idle")
            return f"Error calling LLM: {e}"

        # Try to parse a JSON object out of LLM raw output (robust extraction)
        json_obj = await self.extract_json_from_llm(raw_llm)

        # fallback behavior: if JSON not found, try to repair and parse with repair_json
        if not json_obj:
            try:
                parsed, cleaned, explanation = repair_json(raw_llm)
                json_obj = parsed
            except Exception:
                json_obj = None

        # If still no json and LLM returned code — treat as raw code path (legacy fallback)
        if not json_obj:
            output = await self.process_llm_nonjson(json_obj, question, reuse_rows, df)
            return output
        
        output = await self.process_llm_json(json_obj, question, reuse_rows, df) 
        return output

    async def get_context(self, use_memory:bool, question: str) -> Tuple[str, bool]:
        stm_context = ""
        try:
            # If agent has conversation memory built into some other component,
            # you can hook it here. For v16 standalone we skip or keep empty.
            if use_memory and hasattr(self, "get_memory_context"):
                stm_context = self.get_memory_context(question, char_budget=2000) or ""
        except Exception:
            stm_context = ""

        # --- STEP 2: Retrieve semantic SDCM memory
        sdc_context = ""
        try:
            if use_memory:
                # SDCM returns a list of relevant docs or a string summary
                hits = self.sdcm.retrieve_similar(question, top_k=3)
                # build text block similar to old LTM block
                if hits:
                    sdc_context = "\n".join([f"[SDCM] {h}" for h in hits])
        except Exception:
            sdc_context = ""

        # --- Decide whether to reuse previous filtered rows (same semantics as before)
        reuse_rows = False
        context_rows_df = None
        if self.refers_to_previous_context(question) and getattr(self, "_last_context_rows", None) is not None:
            reuse_rows = True
            context_rows_df = self._last_context_rows

        # --- STEP 3: Build combined_context exactly like v15 (STM first, then SDCM)
        combined_context = ""
        if stm_context:
            combined_context += f"\n[Short-Term Memory]\n{stm_context}\n"
        if sdc_context:
            combined_context += f"\n[Structured Data Memory]\n{sdc_context}\n"

        print(f"Combined context:\n{combined_context}")

        return combined_context, reuse_rows
    
    async def prepare_prompt(self, preview:str, question: str, combined_context: str) -> str:
        prompt_template = Template(textwrap.dedent(f"""
        Based on the following dataframe and the conversation history, answer the user query.
        The dataframe is already loaded as `df`.
        Provide only a JSON object (no additional text). The JSON must contain these keys:
        - action: one of ["code","rows","answer"].
        - code: (string) valid Python (pandas) code to run which will compute the answer. 
        If you return code, ensure final answer is saved into a variable named 'result'.
        - rows_filter: (optional) a short pandas-style boolean expression.
        (e.g., "company == 'Company A'") that can be used to filter df.
        - target_columns: a list of column names that the user is asking for.
        - explain: (optional) short explanation (1-2 sentences).
        Rules:
        - If the user asks about a specific columns, include only those columns.
        - If the user asks about multiple attributes, return all relevant columns.
        - If the user asks a broad question (e.g. "show details"), return an empty list.
        - Column names must match the CSV columns exactly.
        - Do not create new column names.
        Example:

        User: "Give me the model name where primary use case is image generation."

        Your output:
        {{
        "action": "rows",
        "rows_filter": "Primary Use Case == 'Image Generation'",
        "target_columns": ["Model Name"]
        }}

        User: "Which developers created models for image generation?"

        Your output:
        {{
        "action": "rows",                                                   
        "rows_filter": "Primary Use Case == 'Image Generation'",
        "target_columns": ["Developer"]
        }}           

        User: "Show models with parameters above 1 billion."

        Your output:
        {{
        "action": "rows",                                                   
        "rows_filter": "`Parameters (Billions)` > 1",
        "target_columns": ["Model Name", "Parameters (Billions)"]
        }}

        User: "Show all rows where release year is 2022."

        Your output:
        {{
        "action": "rows",                                                   
        "rows_filter": "`Release Year` == 2022",
        "target_columns": []
        }}                 

        If the user question refers to "those/them/previous", reuse the provided
        previously-used rows passed below.
        Do not access external resources. Avoid any filesystem or network operations.
        Dataset sample (first 5 rows):        
        $preview

        Question: $question

        Relevant conversation context (if any):
        $combined_context

        If you return "action": "rows", include rows_filter or a small csv snippet
        in `code` as CSV string.
        Output strictly parseable JSON.
        """))

        prompt = prompt_template.substitute(
            preview = preview,
            question = question,
            combined_context = combined_context
        )
        return prompt

    async def extract_json_from_llm(self, raw_llm: str)-> Dict[str,Any]:
        raw = raw_llm.strip()
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end != -1 and end > start:
                candidate = raw[start:end]
                json_obj = json.loads(candidate)
                return json_obj
        except Exception:
            json_obj = None
            return json_obj

    async def process_llm_nonjson(self, raw:str, question: str, reuse_rows: bool, df: pd.DataFrame) -> str:
        # attempt to treat the whole response as python code
        try:
            code = self.clean_code_block(raw)
        except Exception:
            code = ""

        if code:
            exec_env = {"df": df, "pd": pd}
            try:
                exec_globals = {"__builtins__": _SAFE_BUILTINS, "pd": pd}
                cleaned_code = self.prepare_code(code)
                with contextlib.redirect_stdout(io.StringIO()) as _tmp_out:
                    exec(cleaned_code, exec_globals, exec_env)

                if "result" in exec_env:
                    result_value = exec_env["result"]
                    result_str = str(result_value)
                else:
                    if "df" in exec_env and isinstance(exec_env["df"], pd.DataFrame):
                        self._last_context_rows = exec_env["df"].copy()
                        result_str = f"Returned {len(self._last_context_rows)} rows (preview attached)."
                    else:
                        result_str = "Code executed; no `result` variable found."

                # store semantic memory in SDCM
                try:
                    self.sdcm.add_memory(f"Q: {question}\nA: {result_str}", {"file_name": self.filename})
                except Exception:
                    pass

                await self._set_status("idle")
                self._last_result = result_str
                return result_str

            except Exception as e:
                # record failure in memory as well
                try:
                    self.sdcm.add_memory(f"Q: {question}\nA: Error executing code: {e}", {"file_name": self.filename})
                except Exception:
                    pass
                await self._set_status("idle")
                return f"Error executing code: {e}"

        await self._set_status("idle")
        return "Could not parse LLM response."

    async def process_llm_json(self, json_obj: Dict[str, Any], question: str, reuse_rows: bool, df: pd.DataFrame)-> str:
        # --- Now we have a JSON object from the LLM
        action = json_obj.get("action")
        code = json_obj.get("code", "")
        rows_filter = json_obj.get("rows_filter")
        explain = json_obj.get("explain", "")
        target_columns = json_obj.get("target_columns", "")

        # If the LLM suggests a rows_filter and we didn't reuse rows,
        # apply it to build context_rows_df
        if rows_filter and not reuse_rows:
            try:
                context_rows_df = df.query(rows_filter)
                self._last_context_rows = context_rows_df.copy()
            except Exception:
                context_rows_df = None

        # ACTION: rows
        if action == "rows":
            if context_rows_df is None:
                # LLM might have provided CSV in code
                if code:
                    try:
                        from io import StringIO
                        tmp = pd.read_csv(StringIO(code))
                        self._last_context_rows = tmp
                        preview_rows = tmp.head(50).to_csv(index=False)
                        # store in SDCM
                        try:
                            self.sdcm.add_memory(f"Q: {question}\nA: Provided rows ({len(tmp)}).", {"file_name": self.filename})
                        except Exception:
                            pass
                        await self._set_status("idle")
                        return preview_rows
                    except Exception as e:
                        await self._set_status("idle")
                        return f"Could not parse rows returned by agent: {e}"

                if rows_filter:
                    try:
                        filter_expr = self.clean_filter(rows_filter)
                        filtered_df = df.query(filter_expr)
                        if target_columns:
                            # target_columns may be empty list -> full
                            reduced_df = filtered_df[target_columns]
                            # store
                            try:
                                self.sdcm.add_memory(f"Q: {question}\nA: Returned {len(reduced_df)} rows", {"file_name": self.filename})
                            except Exception:
                                pass
                            return reduced_df.to_markdown(index=False)
                        return filtered_df.to_markdown(index=False)
                    except Exception as e:
                        return {"error": f"failed to apply rows_filter: {rows_filter}", "details": str(e)}

                await self._set_status("idle")
                return "No rows could be generated."
            else:
                preview_rows = context_rows_df.head(50).to_csv(index=False)
                try:
                    self.sdcm.add_memory(f"Q: {question}\nA: Provided rows ({len(context_rows_df)}).", {"file_name": self.filename})
                except Exception:
                    pass
                await self._set_status("idle")
                return preview_rows

        # ACTION: code / answer
        if action in ("code", "answer"):
            if not code:
                ans = explain or "No code or answer provided."
                try:
                    self.sdcm.add_memory(f"Q: {question}\nA: {ans}", {"file_name": self.filename})
                except Exception:
                    pass
                await self._set_status("idle")
                return ans

            # execute code safely
            exec_env = {"df": df, "pd": pd}
            try:
                exec_globals = {"__builtins__": _SAFE_BUILTINS, "pd": pd}
                cleaned_code = self.prepare_code(code)
                with contextlib.redirect_stdout(io.StringIO()) as _tmp_out:
                    exec(cleaned_code, exec_globals, exec_env)

                if "result" in exec_env:
                    result_value = exec_env["result"]
                    result_str = str(result_value)
                else:
                    if "filtered_df" in exec_env and isinstance(exec_env["filtered_df"], pd.DataFrame):
                        self._last_context_rows = exec_env["filtered_df"].copy()
                        result_str = f"Returned {len(self._last_context_rows)} rows (preview attached)."
                    else:
                        result_str = "Code executed; no `result` variable found."

                # store in SDCM
                try:
                    self.sdcm.add_memory(f"Q: {question}\nA: {result_str}", {"file_name": self.filename})
                except Exception:
                    pass

                await self._set_status("idle")
                self._last_result = result_str
                return result_str

            except Exception as e:
                try:
                    self.sdcm.add_memory(f"Q: {question}\nA: Error executing code: {e}", {"file_name": self.filename})
                except Exception:
                    pass
                await self._set_status("idle")
                return f"Error executing code: {e}"

        # Fallback
        await self._set_status("idle")
        return "Could not interpret agent response."        