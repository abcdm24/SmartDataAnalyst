import code
from core.llm_client import ask_llm
import pandas as pd
import io
import contextlib
import re
import gc
import sys
from typing import List
import asyncio
from core.config import MODEL_BUDGETS

class Agent_v13:

    def __init__(self, *, model_name="gpt3.5-turbo", memory_max_items: int = 8, memory_summarize_threshold: int = 20):
        self.model_config = MODEL_BUDGETS.get(model_name)
        self._last_exec_env = None
        self._last_buffer = None
        self._last_result = None

        self.conversation_memory: List[dict] = []
        self.memory_summary: str | None = None

        self.memory_max_items = memory_max_items
        self.memory_summarize_threshold = memory_summarize_threshold

        self._summarizing = False
        self.add_count = 0


    def clean_code_block(self, text: str) -> str:
        """
        Extracts clean python code from LLM responses
        that may contain markdown fences or extra text.
        """
        if not isinstance(text, str):
            return ""
        code_block = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        return text.strip()        
    

    def cleanup(self, local_vars: dict | None = None, output_buffer: io.StringIO | None = None):
        """
        Safely clean up in-memory objects and buffers after execution.

        Backwards-compatible signature: accepts optional local_vars and output_buffer.
        Also cleans up any internal references that the Agent kept.
        """
        try:
            # Close and remove any provided output_buffer
            if output_buffer is not None:
                try:
                    output_buffer.close()
                except Exception:
                    # best-effort close; ignore failures
                    pass
                output_buffer = None

            # Clear provided local_vars if present
            if isinstance(local_vars, dict):
                try:
                    local_vars.clear()
                except Exception:
                    pass
                local_vars = None

            # Clear internal references the Agent may have kept
            try:
                if getattr(self, "_last_buffer", None) is not None:
                    try:
                        self._last_buffer.close()
                    except Exception:
                        pass
                    self._last_buffer = None
            except Exception:
                pass

            try:
                self._last_exec_env = None
            except Exception:
                pass

            try:
                self._last_result = None
            except Exception:
                pass

            # Remove any temporary module entries if created by exec (defensive)
            try:
                sys.modules.pop("__temp_exec_env__", None)
            except Exception:
                pass

            # Run garbage collection (best-effort)
            try:
                gc.collect()
            except Exception:
                pass

        except Exception as e:
            # Never raise from cleanup; print a warning for visibility
            print(f"Cleanup warning: {e}")

    #---------------------
    # Memory Management
    #---------------------

    def add_to_memory(self, question: str, answer: str):
        """
        Add a Q/A pair into conversation memory and trigger summarization
        if memory grows too large.
        """

        if question is None or answer is None:
            return
        
        self.conversation_memory.append({"q": str(question), "a": str(answer)})
        
        # Always enforce hard trimming based on token/char limits
        self._trim_memory_if_needed()

        self.turn_count = getattr(self, "turn_count", 0) + 1

        summarize_every = getattr(self.model_config, "summarize_every", 3)
        
        # Keep only recent items if longer than memory_max_items
        #if len(self.conversation_memory) > self.memory_max_items * 3:
        #    self.conversation_memory = self.conversation_memory[-self.memory_max_items :]            


        # Trigger summarization when we accumulate many items
        #if len(self.conversation_memory) >= self.memory_summarize_threshold  and not self._summarizing:
        # Summarize every N turns (configurable)
        if self.turn_count % summarize_every == 0:
            try:
                # self.summarize_memory()
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_summarize_memory())
            except Exception:
                # Ignore summarization failures
                asyncio.run(self._async_summarize_memory())


    def _trim_memory_if_needed(self):
        """Trim memory if character length exceed configured budget."""
        config = self.model_config
        if not config:
            return
        
        text = "\n".join(
            f"Q: {m['q']}\nA: {m['a']}" for m in self.conversation_memory
        )

        total_chars = len(text)

        while total_chars > config.max_chars and len(self.conversation_memory) > 1:
            self.conversation_memory.pop(0)
            text = "\n".join(
                f"Q: {m['q']}\nA: {m['a']}" for m in self.conversation_memory
            )
            total_chars = len(text)

        if total_chars > config.max_chars:
            print(f"[MemoryTrim] Warning: still over budget ({total_chars} chars)")    
            

    async def _async_summarize_memory(self):
        """
        Use the LLM to produce a short summary of conversation memory.
        Stores the summary in self.memory_summary and clears older items.
        """

        if not self.conversation_memory:
            return

        self._summarizing = True       
        # Build a compact text of recent Q/A for summarization
        entries = []

        try:
            for item in self.conversation_memory:
                q = item.get("q", "").replace("\n", " ")
                a = item.get("a", "").replace("\n", " ")
                entries.append(f"Q: {q}\nA: {a}")
            
            joined = "\n\n".join(entries)
            prompt = f"""
            You area concise assistant that summarized a conversation between a user and a 
            data analysis agent. Given the following recent Q/A pairs, produce a short bullet 
            or paragraph summary (1-3 sentence) capturing:
            - The user's main recurring goals
            - Any persistent context (column names, data shapes, filters used)
            - Anything the agent should remember for future follow-ups.

            Conversation:
            {joined}

            Produce a one-to-three sentence summary that can be safely appended to future
            prompts to provide context.
            """

            # Ask the LLM to summarize (best-effort)
            summary = None
            try:
                summary = await ask_llm(prompt)
            except Exception:
                summary = None

            # Clean up and store
            if summary:
                self.memory_summary = (summary or "").strip()
                # After summarization, prune conversation memory 
                # to the most recent few   
                self.conversation_memory = self.conversation_memory[-self.memory_max_items :]         
            else:
                # if summarization failed, keep memory as-is (no harm)
                pass
        except Exception as e:        
            print(f"[warn] memory summarization failed: {e}")
        finally:
            self._summarizing = False
    
    def get_memory_context(self, question: str, char_budget: int = 2000) -> str:
        """
        Build a compact memory block to include in prompts.
        Prefers: memory_summary + up to N recent Q/A pairs,
        trimmed to char_budget.
        """
        parts = []
        if self.memory_summary:
            parts.append("Summary of conversation so far: " + self.memory_summary)


        # Use most recent items first
        for item in reversed(self.conversation_memory[-self.memory_max_items :]):
            q = item.get("q","")
            a = item.get("a","")
            parts.append(f"USER: {q}\nAGENT: {a}")

        context = "\n\n".join(reversed(parts)) if parts else ""

        # Trim to char-budget conservatively
        if len(context) > char_budget:
            conetxt = context[-char_budget:]
            # try to avoid cutting in middle of a tocken by taking last full lines
            lines = context.splitlines()
            context = "\n".join(lines[-min(len(lines), 30):])
        return context
    

    #---------------------
    # Analyze query (main execution path)
    #---------------------
    async def analyze_query(self, df: pd.DataFrame, question: str, use_memory: bool = True) -> str:
        """
        Executes the question by askig the LLM for python (pandas) code and running it.
        If use_memory = True, injects compact memory context into the LLM prompt.
        Returns string (either result or "Error executing code: ...")
        """

        preview = df.head(5).to_csv(index=False)

        memory_block = ""
        if use_memory:
            memory_block = self.get_memory_context(question, char_budget=2000)

        prompt = f"""
        You are a data analyst assistant.
        Given the following dataset (first 5 rows) and a user question,
        generate valid executable Python (pandas) code that computes the answer.
        The dataframe is already loaded as `df`.

        Dataset sample:
        {preview}

        Question: {question}

        """

        if memory_block:
            prompt += f"\nRelevant conversation context:\n{memory_block}\n\n"

        prompt += """
        Output only Python code - no explanation or markdown text.
        If Calculation is required, store final answer in a variable named `result`.
        """

        # Step 2: Get code from LLM
        try:
            raw_code = await ask_llm(prompt)
        except Exception as e:
            self.cleanup(None,None)
            return f"Error calling LLM: {e}"
        
        code = self.clean_code_block(raw_code)
        print("Generated code:\n", code)
        print("df: ", df.head(10))
        # Execute in isolated namespace
        exec_env = {"df": df}
        self.last_exec_env = exec_env
        output_buffer = None

        try:
            output_buffer = io.StringIO()
            self._last_buffer = output_buffer
            with contextlib.redirect_stdout(output_buffer):
                exec(code, {}, exec_env)

            output_text = output_buffer.getvalue()
            print("Captured output:\n", output_text)
            if "result" in exec_env:
                result_value = exec_env ["result"]               
                result_str = str(result_value)
            elif output_text:
                result_str = output_text.strip()
            else:
                result_str = "No output returned."
        
            try:
                self.add_to_memory(question, result_str)
            except Exception:
                pass

            self._last_result = result_str
            return result_str
        
        except Exception as e:
            try:
                self.add_to_memory(question, f"Error executing code: {e}")
            except Exception:
                pass
            return f"Error executong code: {e}"
    
        finally:
            try:
                if isinstance(self._last_exec_env, dict):
                    try:
                        self._last_exec_env.clear()
                    except Exception:
                        pass
                self.cleanup(exec_env, output_buffer)
                exec_env = None
                output_buffer = None
                gc.collect()
            except Exception:
                pass

    #----------------------------
    # Convenience wrapper for follow-ups
    #----------------------------
    async def ask_followup(self, df: pd.DataFrame, followup_question: str) -> str:
        """
        Convenience method for asking a follow-up question.
        Uses memory by default.
        """
        return await self.analyze_query(df, followup_question, use_memory=True)