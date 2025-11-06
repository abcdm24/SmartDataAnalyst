# import openai
# import os
#
# openai.api_key = os.getenv("OPENAI_API_KEY")
#
# def ask_llm(prompt: str) -> str:
#     """
#     Simple LLM wrapper - returns raw text response.
#     """
#
#     response = openai.ChatCompletion.create(
#         model = "gpt-4o-mini",
#         messages =[
#             {"role": "system", "content": "You are an expert Python data analyst."},
#             {"role": "user", "content": prompt},
#         ],
#         temperatur=0.2
#     )
#     return response.choices[0].message["content"]