import pytest
import pandas as pd
from core.agent_v16 import Agent_v16

@pytest.mark.asyncio
async def test_extract_valid_json(monkeypatch):
    agent = Agent_v16()

    raw = """
    Here is your response:
    {
        "action": "filter",
        "code": "result = df[df['age'] > 30]"
    }
    """

    # Patch LLM
    monkeypatch.setattr("core.agent_v16.ask_llm", lambda prompt: raw)

    df = pd.DataFrame({"age": [20,40]})
    response = await agent.analyze_query(df, "people older than 30")

    assert "Returned" in response or "executed" in response
