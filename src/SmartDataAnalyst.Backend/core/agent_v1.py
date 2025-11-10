# from core.llm_client import ask_llm
# import pandas as pd
# import io
# import contextlib
# import re

# def analyze_query(df: pd.DataFrame, question: str) -> str:
#     """
#     A lightweight data analyst agent.
#     1. Sends the question + sample of data to LLM.
#     2. LLM responds with Python code to run.
#     3. Safely executes code and returns output.
#     """
#     # step 1: Build prompt
#     preview = df.head(5).to_csv(index=False)
#     prompt = f"""
#     You are a data analyst assistant.
#     Given the following dataset (first 5 rows) and a user question,
#     generate Python (pandas) code that computes the answer.
#     The dataframe is already loaded as `df`.
    
#     Dataset sample:
#     {preview}
    
#     Question: {question}
    
#     Only return Python code, nothing else.
#     """

#     # Step 2: Get Python code from LLM
#     code = ask_llm(prompt)

#     # Step 3: Execute code safely
#     try:
#         local_vars = {"df": df}
#         output_buffer = io.StringIO()
#         with contextlib.redirect_stdout(output_buffer):
#             exec(code, {}, local_vars)
#         output_text = output_buffer.getvalue()

#         # If code defines a variable `result`, use that
#         if "result" in local_vars:
#             return str(local_vars["result"])
#         elif output_text:
#             return output_text.strip()
#         else:
#             return "No output returned."
#     except Exception as e:
#         return f"Error executing code: {e}"

# def clean_code_block(text: str) -> str:
#     """
#     Extracts clean python code from LLM responses
#     that may contain markdown fences or extra text.
#     """

#     Remove Markdown code fences if present
#     code_block = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
#     if code_block:
#         return code_block.group(1).strip()
#     Otherwise, return the original (stripped)
#     return text.strip()

#     if text.startswith("```") and text.endswith("```"):
#         # Remove the triple backticks
#         text = text[3:-3]
#         # If there's a language specifier, remove it
#         if text.startswith("python\n"):
#             text = text[len("python\n"):]
#     return text.strip()

# def analyze_query(df: pd.DataFrame, question: str) -> str:
#     """
#     A lightweight data analyst agent.
#     1. Sends the question + sample of data to LLM.
#     2. Receives python (Pandas) code
#     3. Executes code safely
#     4. Returns result
#     """
#     # step 1: Build prompt
#     preview = df.head(5).to_csv(index=False)
#     prompt = f"""
#     You are a data analyst assistant.
#     Given the following dataset (first 5 rows) and a user question,
#     generate valid executable Python (pandas) code that computes the answer.
#     The dataframe is already loaded as `df`.
    
#     Dataset sample:
#     {preview}
    
#     Question: {question}

#     Output only Python code - no explanation or markdown text.
#     If Calculation is required, store final answer in a variable named `result`.
#     """

#     # Step 2: Get Python code from LLM
#     code = ask_llm(prompt)

#     # Clean and extract pure code
#     code = clean_code_block(code)

#     # Debug print (optional)
#     print("-----LLM Generated Code-----")
#     print(code)
#     print("---------------------------")

#     # Step 3: Execute code safely
#     try:
#         local_vars = {"df": df}
#         output_buffer = io.StringIO()
#         with contextlib.redirect_stdout(output_buffer):
#             exec(code, {}, local_vars)
#         output_text = output_buffer.getvalue()

#         # If code defines a variable `result`, use that
#         if "result" in local_vars:
#             return str(local_vars["result"])
#         elif output_text:
#             return output_text.strip()
#         else:
#             return "No output returned."
#     except Exception as e:
#         return f"Error executing code: {e}"
