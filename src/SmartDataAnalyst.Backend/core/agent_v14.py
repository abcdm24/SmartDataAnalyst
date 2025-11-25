from .agent_v13 import Agent_v13
from memory.retriever import ContextRetriever
import io, contextlib, gc, pandas as pd
from .llm_client import ask_llm
import time
import asyncio

class Agent_v14(Agent_v13):
    """
    Agent_v14 enhances Agent_v13 by adding Long-Term Memory (FAISS-based)
    retrieval and persistence. It combines short-term context and long-term 
    knowledge grounding for more intelligent analysis.
    """

    def __init__(self, filename: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    
    async def _set_status(self, new_status: str):

        if self.status != new_status and new_status == "idle":
            await asyncio.sleep(2)

        self.status = new_status
        self.last_activity_time = time.time()
        print(f"[Agent_v14] Status changed -> {new_status}")
        if self.on_status_change:   
            try:
                self.on_status_change(self.filename, new_status)
            except Exception as e:
                print(f"[Agent_v14] Status callback error: {e}")
            

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
            stm_context = self.get_memory_context(question, char_budget=2000)


        # --- STEP 2: Retrieve long-term memory ---
        ltm_context = ""
        try:
            ltm_context = self.retrieve.retrieve_context(question, top_k=3)
        except Exception:
            pass            


        # --- STEP 3: Merge context blocks ---
        combined_context = ""
        if stm_context:
            combined_context += f"\n[Short-Term Memory]\n{stm_context}\n"
        if ltm_context:
            combined_context += f"\n[Long-Term Memory]\n{ltm_context}\n"

        prompt = f"""
        You are a data analyst assistant.
        Given the following dataset (first 5 rows) and a user question,
        generate valid executable Python (pandas) code that computes the answer.
        The dataframe is already loaded as `df`.

        Dataset sample:
        {preview}

        Question: {question}

        """

        if combined_context:
            prompt += f"\nRelevant conversation context:\n{combined_context}\n\n"

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
                await self._set_status("summarizing")
                await asyncio.sleep(2)
                
                # Short-term
                self.add_to_memory(question, result_str)
                # Long-term
                self.retriever.add_context(f"Q: {question}\nA: {result_str}")
                # Save FAISS index for persistence
                self.retriever.memory.save(self.faiss_index_path)
            except Exception:
                pass

            await self._set_status("idle")
            
            self._last_result = result_str
            return result_str
        
        except Exception as e:
            try:
                self.add_to_memory(question, f"Error executing code: {e}")
                self.retriever.add_context(f"Q: {question}\nA: Error {e}")
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

    def get_status(self):
        # return "active" if self.status else "idle"
        # print(f"{time.time()} - {self.last_activity_time}")
        if time.time() - self.last_activity_time > 120:
            return "idle"
        return self.status
                