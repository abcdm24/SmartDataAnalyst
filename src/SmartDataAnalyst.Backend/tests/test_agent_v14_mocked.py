import pytest
import pandas as pd
import asyncio
from core.agent_v14 import Agent_v14
import re


@pytest.mark.asyncio
async def test_analyze_query_mocked(monkeypatch):
    """
    Offline test: mocks the LLM call to test Agent_v14 memory logic
    without calling OpenAI.
    1. Ask initial question (highest population city)
    2. Ask a recall question (context grounding)
    3. Ask a follow-up query using contextual memory ("lowercase")
    """

    # --- Step 1: Create test datafrmae ---
    df = pd.DataFrame({
        "City": ["London", "Paris", "Tokyo"],
        "Population": [9_000_000, 2_100_000, 14_000_000]
    })

    # --- Step 2: Create agent instance ---
    agent = Agent_v14()

    # --- Step 3: Mock the LLM call to return fake code ---
    async def fake_llm(prompt):
        print(f"\n--- FAKE LLM PROMPT ---\n{prompt}\n", flush=True)
        match = re.search(r"Question:(.*?)(?:Relevant|Output|$)", prompt, re.DOTALL | re.IGNORECASE)
        question_text = match.group(1).strip().lower() if match else prompt.lower()
        prompt_lower = prompt.lower().replace("\r","").replace("\n"," ")
        # Pretend LLM alwys returns simple code
        if "highest" in question_text:
            # For the first query
            print("-> returning highest-population code")
            return "result = df.loc[df['Population'].idxmax(), 'City']"
        elif "lowercase" in question_text:
            # Third query use last memory (simulated by context injection)
            print("-> returning lowercase result manually")
            return "result = 'tokyo'"
        elif "remind" in question_text or "earlier" in question_text:
            print("-> returning recall memory response")
            return "result = 'Previously, Tokyo had the highest population.'"
        else:
            # Second query: recall the previous answer
            print("-> returning recall memory response")
            return "result = 'Previously, Tokyo had the highest population."
    
    monkeypatch.setattr("core.llm_client.ask_llm", fake_llm)

    # --- Step 4: Run first query ---
    question_1 = "Which city has the highest population?"
    result_1 = await agent.analyze_query(df, question_1)
    print("\nMocked result 1:", result_1)
    assert "14" in result_1 or "Tokyo" in result_1

    # --- Step 5: Run follow-up query (should recall memory) ---
    question_2 = "Remind me what we learned earlier."
    result_2 = await agent.analyze_query(df, question_2)
    print("\nMocked result 2:", result_2)
    assert "Tokyo" in result_2 or "previously" in result_2

    
    # --- Step 6: Run third query (contextual reasoning) ---
    question_3 = "Now show me that in lowercase."
    result_3 = await agent.analyze_query(df, question_3)
    print(f"\nResult 3: {result_3}")
    assert result_3.strip().lower() == "tokyo"


    # --- Setup 7: Inspect FAISS memory contents ---
    print("\n--- Long-term Memory Inspection ---")
    for i, text in enumerate(agent.retriever.memory.texts):
        print(f"[{i}] {text[:200]}...")
    print("-------------------------------\n")

    # --- Setup 8: Inspect memory contens ---
    print("\n--- Agent Memory ---")
    for i, m in enumerate(agent.conversation_memory[-2:]):
        print(f"[{i}] Q: {m['q']} | A: {m['a']}")
    
