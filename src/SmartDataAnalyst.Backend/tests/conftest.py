import sys
import os
import pathlib
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]

sys.path.append(str(PROJECT_ROOT))

print(f"Added to sys.path: {PROJECT_ROOT}")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_llm():
    """
    Automatically mock llm_client.ask_llm for every test.
    Prevents readl Azure/OpenAI calls.
    """

    with patch("src.SmartDataAnalyst.Backend.core.llm_client.ask_llm", AsyncMock(return_value='{"action":"done"}')):
        yield