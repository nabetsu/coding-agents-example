import os

import pytest

import main


@pytest.mark.integration
@pytest.mark.anyio
async def test_agent_lists_python_files():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = main.build_agent()
    async with agent:
        result = await agent.run("List Python files in the current directory.")

    output = getattr(result, "data", None) or str(result)
    assert "main.py" in output
