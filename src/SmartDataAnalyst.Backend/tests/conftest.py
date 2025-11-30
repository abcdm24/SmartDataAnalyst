import sys
import os
import pathlib
import pytest
import asyncio


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]

sys.path.append(str(PROJECT_ROOT))

print(f"Added to sys.path: {PROJECT_ROOT}")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()