# import os
# import io
# import pytest
# import pandas as pd
# from core.agent_v12 import Agent_v12

# @pytest.fixture
# def agent_instance():
#     agent = Agent_v12()
#     yield agent
#     agent.cleanup({}, None)  # Ensure cleanup after each test


# def test_cleanup_closes_buffer_and_clears_vars(agent_instance):
#     """Ensure cleanup closes buffers and clears variables safely."""
#     local_vars = {"df": pd.DataFrame({"x": [1,2,3]}), "temp": 42}
#     output_buffer = io.StringIO("test output")

#     agent_instance.cleanup(local_vars, output_buffer)

#     # Check buffer is closed
#     with pytest.raises(ValueError):
#         output_buffer.write("should fail after close")


#     # Check local_vars cleared
#     assert len(local_vars) == 0, "local_vars was not cleared"


# def test_cleanup_safe_if_none(agent_instance):
#     """Ensure cleanup runs safely with None values.""" 
#     try:
#         agent_instance.cleanup(None, None)
#     except Exception as e:
#         pytest.fail(f"cleanup raised an unexpected exception: {e}")

# def test_analyze_query_valid_code(monkeypatch):
#     """Mock LLm and verify analyze_query executes correctly."""
#     # Mock LLM to return valid python code
#     monkeypatch.setattr("core.agent_v12.ask_llm", lambda prompt: "result = len(df)")

#     df = pd.DataFrame({"a":[1,2,3]})
#     agent = Agent_v12()
#     result = agent.analyze_query(df, "Count rows")

#     assert result == "3", f"Unexpected result: {result}"


# def test_analyze_query_invalid_code(monkeypatch):
#     """Ensure analyze_query handles code errors gracefully."""
#     monkeypatch.setattr("core.agent_v12.ask_llm", lambda prompt: "invalid code here")

#     df = pd.DataFrame({"a":[1,2,3]})
#     agent = Agent_v12()
#     result = agent.analyze_query(df, "This will fail")

#     assert "Error executing code" in result

# def test_cleanup_called_in_finally(monkeypatch):
#     """Verify that cleanup is called even when execution fails."""

#     agent = Agent_v12()
#     df = pd.DataFrame({"a": [1,2,3]})
#     cleanup_called = {}

#     def mock_cleanup(local_vars, output_buffer):
#         cleanup_called["called"] = True

#     # Force LLM to return bad code to trigger execution
#     monkeypatch.setattr("core.agent_v12.ask_llm", lambda prompt: "raise Exception('oops')")
#     monkeypatch.setattr(agent, "cleanup", mock_cleanup)

#     _ = agent.analyze_query(df, "trigger error")

#     assert cleanup_called.get("called", False), "cleanup() was not called in finally block"