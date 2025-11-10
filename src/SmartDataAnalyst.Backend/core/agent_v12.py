from core.llm_client import ask_llm
import pandas as pd
import io
import contextlib
import re
import gc
import sys


class Agent_v12:
    def __init__(self):
        # Optional persistent attributes
        self._last_exec_env = None
        self._last_buffer = None
        self._last_result = None
        # For debugging when needed
        # print("constructor called")

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

    def analyze_query(self, df: pd.DataFrame, question: str) -> str:
        """
        A lightweight data analyst agent (class-based).
        1. Sends the question + sample of data to LLM.
        2. Receives python (Pandas) code
        3. Executes code safely in an isolated namespace
        4. Returns result as string
        """
        # prepare prompt (keep small sample to reduce token sizes)
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
        try:
            raw_code = ask_llm(prompt)
        except Exception as e:
            # If LLM call fails, ensure cleanup and return error string
            self.cleanup(None, None)
            return f"Error calling LLM: {e}"

        code = self.clean_code_block(raw_code)

        # Debug print (optional)
        print("-----LLM Generated Code-----")
        print(code)
        print("---------------------------")

        # Prepare isolated execution environment
        exec_env = {"df": df}
        self._last_exec_env = exec_env  # keep reference briefly in case of inspection
        output_buffer = None

        try:
            # Capture stdout from executed code to output_buffer
            output_buffer = io.StringIO()
            self._last_buffer = output_buffer
            with contextlib.redirect_stdout(output_buffer):
                # Execute in a fresh local namespace to avoid polluting global scope
                exec(code, {}, exec_env)

            output_text = output_buffer.getvalue()

            # If code defined a variable `result`, return that
            if "result" in exec_env:
                result_value = exec_env["result"]
                # Normalize result to string
                self._last_result = str(result_value)
                return self._last_result
            elif output_text:
                self._last_result = output_text.strip()
                return self._last_result
            else:
                self._last_result = "No output returned."
                return self._last_result

        except Exception as e:
            # Return a clear error message as string
            return f"Error executing code: {e}"
        finally:
            # Ensure we always run cleanup and remove exec_env
            try:
                # Clear exec_env contents first (defensive)
                if isinstance(self._last_exec_env, dict):
                    try:
                        self._last_exec_env.clear()
                    except Exception:
                        pass
                # Call cleanup (backwards-compatible)
                self.cleanup(exec_env, output_buffer)
                # Remove local references
                exec_env = None
                output_buffer = None
                gc.collect()
            except Exception:
                # Never re-raise cleanup exceptions
                pass
