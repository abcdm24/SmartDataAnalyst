from core.llm_client import ask_llm
import pandas as pd
import io
import contextlib
import re
import gc

class Agent_v11:

    def __init__(self):
        print("constructor called")

        
    def clean_code_block(self, text: str) -> str:
        """
        Extracts clean python code from LLM responses
        that may contain markdown fences or extra text.
        """

        # Remove Markdown code fences if present
        code_block = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        # Otherwise, return the original (stripped)
        return text.strip()


    def cleanup(self, local_vars: dict, output_buffer: io.StringIO):
        """
        Safely clean up in-memory objects and buffers after execution
        """

        try:    
            if output_buffer:
                output_buffer.close()
            # Clear temporary variables and free memory
            local_vars.clear()
            gc.collect()
        except Exception as e:
            print(f"Cleanup warning: {e}")
    

    def analyze_query(self, df: pd.DataFrame, question: str) -> str:
        """
        A lightweight data analyst agent.
        1. Sends the question + sample of data to LLM.
        2. Receives python (Pandas) code
        3. Executes code safely
        4. Returns result
        """
        # step 1: Build prompt
        preview = df.head(5).to_csv(index=False)
        prompt = f"""
        You are a data analyst assistant.
        Given the following dataset (first 5 rows) and a user question,
        generate valid executable Python (pandas) code that computes the answer.
        The dataframe is already loaded as `df`.
        
        Dataset sample:
        {preview}
        
        Question: {question}

        Output only Python code - no explanation or markdown text.
        If Calculation is required, store final answer in a variable named `result`.
        """

        # Step 2: Get Python code from LLM
        code = ask_llm(prompt)

        # Clean and extract pure code
        code = self.clean_code_block(code)

        # Debug print (optional)
        print("-----LLM Generated Code-----")
        print(code)
        print("---------------------------")

        output_buffer = None
        local_vars = {"df": df}

        # Step 3: Execute code safely
        try:
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                exec(code, {}, local_vars)
            output_text = output_buffer.getvalue()

            # If code defines a variable `result`, use that
            if "result" in local_vars:
                return str(local_vars["result"])
            elif output_text:
                return output_text.strip()
            else:
                return "No output returned."
        except Exception as e:
            return f"Error executing code: {e}"
        finally:
            # Ensure cleanup always runs
            self.cleanup(local_vars, output_buffer)

