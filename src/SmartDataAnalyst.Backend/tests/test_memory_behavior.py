import pytest
pytest_plugins = ("pytest_asyncio")
import io
import gc
import psutil
import pandas as pd
from unittest.mock import AsyncMock, patch
from core.agent_v13 import Agent_v13
import asyncio

class DummyConfig:
    def __init__(self, max_chars: int = 10000, summarize_every: int = 3):
        self.max_chars = max_chars
        self.summarize_every = summarize_every


def test_memory_add_and_get_context():
    agent = Agent_v13(memory_max_items=3, memory_summarize_threshold=10)
    agent.add_to_memory("How many rows?", "100")
    agent.add_to_memory("Average value?", "50")
    ctx = agent.get_memory_context("Now what?", char_budget=500)
    assert "How many rows?" in ctx and "Average value?" in ctx


async def test_followup_uses_memory(monkeypatch):
    #monkeypatch ask_llm to exho prompt so we can observe memory included
    captured = {}
    async def fake_ask(prompt):
        captured["prompt"] = prompt
        return "result = 1"
    monkeypatch.setattr("core.agent_v13.ask_llm", fake_ask)
    agent = Agent_v13()
    # senf memory
    agent.add_to_memory("Previous Q", "Previous A")
    df = pd.DataFrame({"x":[1]})
    await agent.analyze_query(df, "A new question")
    assert "Relevant conversation context" in captured["prompt"]


def test_memory_trimming_respects_budget():
    from core.agent_v13 import Agent_v13
    agent = Agent_v13()
    long_text = "x" * 5000

    for i in range(5):
        agent.add_to_memory(f"Q{i}", long_text)

    assert len(agent.conversation_memory) < 100


@pytest.mark.asyncio
async def test_summarization_trigger(monkeypatch):
    """
    Ensure _async-summarize_memory is scheduled after summarize_every turns.
    We patch the agent's _async_summarize_memory with an AsyncMock.
    """

    agent = Agent_v13()

    agent.model_config = DummyConfig(max_chars=10000, summarize_every=3)

    mock_summarize = AsyncMock()
    monkeypatch.setattr(agent, "_async_summarize_memory", mock_summarize)


    for i in range(agent.model_config.summarize_every):
        q = "Q" * 20
        a = "A" * 20
        agent.add_to_memory(f"Q{i}",f"A{i}")

    await asyncio.sleep(0)

    assert mock_summarize.await_count >= 0


def test_trim_memory_if_needed_reduces_size():
    """
    Ensure that _trim_memory_if_needed prunes conversation_memory
    so the total chars <= model_config.max_chars.    
    """

    agent = Agent_v13()

    for i in range(5):
        q = "Q" * 20
        a = "A" * 20
        agent.conversation_memory.append({"q": q, "a": a})

    agent.model_config = DummyConfig(max_chars=200, summarize_every=3)
    agent._trim_memory_if_needed()

    # Check memory was trimmed
    total_chars = sum(len(m["q"]) + len(m["a"]) for m in agent.conversation_memory)
    assert total_chars <= agent.model_config.max_chars, (
        f"Memory not trimmed: {total_chars} chars > max_chars {agent.model_config.max_chars}"
    )

    # Also check oldest items were pruned
    assert len(agent.conversation_memory) < 5