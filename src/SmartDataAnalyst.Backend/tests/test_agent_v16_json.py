# import pytest
# import pandas as pd
# from core.agent_v16 import Agent_v16

# @pytest.mark.asyncio
# async def test_extract_valid_json(monkeypatch):
#     agent = Agent_v16("movie_ratings.csv")

#     raw = """
#     {
#         "action": "code",
#         "code": "result = df[df['age'] > 30]"
#     }
#     """

#     # raw = """{"action": "code", "code": "result = df[df['age'] > 30]"}"""

#     async def fake_llm(prompt: str):
#         return raw

#     # Patch LLM
#     monkeypatch.setattr("core.agent_v16.ask_llm", fake_llm)

#     df = pd.DataFrame({"age": [20,40]})
#     response = await agent.analyze_query(df, "people older than 30")

#     print(f"response: {response}")
#     #assert "Returned" in response or "executed" in response
#     assert "age" in response or "40" in response
