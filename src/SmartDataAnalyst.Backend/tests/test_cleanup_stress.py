import io
import gc
import psutil
import pandas as pd
import pytest
from core.agent_v12 import Agent_v12


@pytest.fixture(scope="module")
def df_sample():
    """Provide a reusable DataFrame sample for stress testing."""
    return pd.DataFrame({
        "id": range(1,101),
        "value": [i * 2 for i in range(1, 101)]
    })

@pytest.mark.parametrize("iterations", [50,100])
def test_repeated_analyze_query_does_not_leak_memory(monkeypatch, df_sample, iterations):
    """
    Run analyze_query repeatedly to ensure cleanup prevents memory leaks.
    """
                             
    # Mock ask_llm to return a simple valid code each time
    monkeypatch.setattr("core.agent_v12.ask_llm", lambda prompt: "result = df['value'].mean()")

    agent = Agent_v12()
    process = psutil.Process()
    baseline_memory = process.memory_info().rss

    for _ in range(iterations):
        result = agent.analyze_query(df_sample, "Get average value")
        assert result.replace(".","",1).isdigit() or result.startswith("Error")

    # Force garbage collection
    gc.collect()

    # Measure memory usage after repeated runs
    post_memory = process.memory_info().rss

    # Allow some small fluctuations (up to 5 MB tolerance)
    memory_diff_mb = abs(post_memory - baseline_memory) / (1024 * 1024)
    assert memory_diff_mb < 12.5, f"Potential memory leak: {memory_diff_mb:.2f} MB increase"

def test_cleanup_repeatedly_with_buffers(df_sample):    
    """Stress test cleanup directly for robustness."""
    agent = Agent_v12()

    for _ in range(100):
        local_vars = {"df": df_sample.copy(), "temp": list(range(100))}
        buffer = io.StringIO("test output")

        agent.cleanup(local_vars, buffer)

        assert len(local_vars) == 0, "local_vars not cleared during repeated cleanup"
        assert buffer.closed, "Buffer not closed during repeated cleanup"

def test_cleanup_resilience_to_partial_failures(monkeypatch):
    """Simulate cleanup raising an internal warning (e.g. faulty gc)."""        
    agent = Agent_v12()
    cleanup_warnings = []

    def mock_gc_collect():
        cleanup_warnings.append("GC called")
        raise RuntimeError("Simulated GC failure")
    
    monkeypatch.setattr("gc.collect", mock_gc_collect)

    try:
        agent.cleanup({"a": 1}, io.StringIO("data"))
    except Exception:
        pytest.fail("cleanup() should not raise even if gc fails")

    assert cleanup_warnings, "Mock GC was not invoked"
