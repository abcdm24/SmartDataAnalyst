import os
import pandas as pd
import pytest
import asyncio
from core.agent_v14 import Agent_v14

#--------CONFIG-------------------
FAISS_PATH = "data/memory.index"

@pytest.mark.asyncio
async def test_analyze_query_creates_and_uses_memory(monkeypatch, tmp_path):
    """
    Test Agent_v14 end-to-end:
    1. Runs analyze_query on sample data.
    2. Verifies FAISS index persistence.
    3. Confirms retrieval works across calls.
    """
    print("Starting long-term memory test")
    
    # ---Step 1: Create sample dataframe ---
    data = {
        "Product" : ["Apple", "Banana", "Cherry", "Apple", "Banana"],
        "Sales": [10,15,7,20,30],
        "Region": ["East", "West", "East", "North", "South"]
    }
    df = pd.DataFrame(data)

    # ---------- CLEAN MEMORY ----------
    for f in [FAISS_PATH, FAISS_PATH + ".txt"]:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception as e:
            print(f"Error: {e}")

    # ---------- MOCK ask_llm ----------
    async def fake_llm(prompt: str):
        # print(f"Prompt: {prompt.lower()}")
        # Very deterministic fake results for both queries
        
        if "earlier finding on top sales" in prompt.lower():
            return "result = 'Earlier, we found that Banana had the highest sales.'"
            # return """
            # {
            #     "action": "direct_answer",
            #     "answer": "Banana has the highest total sales."
            # }
            # """
        elif "learned about sales performance earlier." in prompt.lower():
            return "result = df.head(3)"
        elif "highest total sales" in prompt.lower():
            return "result = 'Banana has the highest total sales.'"
            # return """
            # {
            #     "action": "direct_answer",
            #     "answer": "Earlier, we found that Banana had the highest sales."
            # }
            # """
      
    # Patch LLM
    monkeypatch.setattr("core.agent_v14.ask_llm", fake_llm)
     

    # --- Step 2: Initialize agent ---
    agent = Agent_v14("movie_ratings.csv")
    #Ensures clean memory for testing
    # if os.path.exists(FAISS_PATH):
    #     try:
    #         os.remove(FAISS_PATH)   
    #         os.remove(FAISS_PATH + ".txt")
    #     except Exception:
    #         pass
    
    # --- Step 3: First query (should generate new FAISS memory) ---
    question_1 = "Which product has the highest total sales?"
    result_1 = await agent.analyze_query(df, question_1)
    print("\nFirst query result:\n", result_1)

    # Validate output
    assert isinstance(result_1, str)
    assert "Error" not in result_1

    # --- Step 4: Check FAISS memory files ---
    assert os.path.exists("/home/runner/work/SmartDataAnalyst/SmartDataAnalyst/data/memory.index"), "FAISS index file not created."
    assert os.path.exists("/home/runner/work/SmartDataAnalyst/SmartDataAnalyst/data/memory.index.txt"), "FAISS text memory not saved."

    # --- Step 5: Second query (should use LTM retrieval) ---
    question_2 = "Remind me what we learned about sales performance earlier."
    result_2 = await agent.analyze_query(df, question_2)
    print("\nSecond query result:\n", result_2)

    # --- Step 6: Verify it produces output and uses memory ---
    assert isinstance(result_2, str)
    #assert len(result_2) > 0
    #assert any(word in result_2.lower() for word in ["apple", "banana", "sales", "result"]), \
    #"Resoponse did not seem to recall past context."
    # assert "earlier" in result_2.lower()
    assert "banana" in result_2.lower()

    # --- Step 7: Confirm persistence services reloading ---
    agent_reload = Agent_v14("movie_ratings.csv")
    result_3 = await agent_reload.analyze_query(df, "What was our earlier finding on top sales?")
    print("\nReloaded agent result:\n", result_3)
    assert isinstance(result_3, str)
    assert len(result_3) > 0

    print("\n Agent_v14 memory persistence test passed.\n")
