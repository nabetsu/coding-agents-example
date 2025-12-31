import asyncio
import os
import tempfile
from pathlib import Path
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv()

instructions = """
You are a specialised agent for maintaining and developing the XXXXXX codebase.

## Development Guidelines:

1. **Test Failures:**
   - When tests fail, fix the implementation first, not the tests
   - Tests represent expected behavior; implementation should conform to tests
   - Only modify tests if they clearly don't match specifications

2. **Code Changes:**
   - Make the smallest possible changes to fix issues
   - Focus on fixing the specific problem rather than rewriting large portions
   - Add unit tests for all new functionality before implementing it

3. **Best Practices:**
   - Keep functions small with a single responsibility
   - Implement proper error handling with appropriate exceptions
   - Be mindful of configuration dependencies in tests

Remember to examine test failure messages carefully to understand the root cause before making any changes.
"""

def build_model(api_key: str | None = None) -> OpenAIChatModel:
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    return OpenAIChatModel("gpt-4o", provider=OpenAIProvider(api_key=api_key))

def _make_code_reasoning_patch() -> str:
    patch_path = Path(tempfile.gettempdir()) / "code_reasoning_stdio_patch.cjs"
    if not patch_path.exists():
        patch_path.write_text(
            "const err = console.error.bind(console);\n"
            "// Keep stdout clean for MCP JSON-RPC.\n"
            "console.log = err;\n"
            "console.info = err;\n",
            encoding="utf-8",
        )
    return str(patch_path)

def build_toolsets() -> list[MCPServerStdio]:
    filesystem_server = MCPServerStdio(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
        env={
            **os.environ,
            "LOG_LEVEL": "error",
        },
    )

    code_reasoning = MCPServerStdio(
        command="npx",
        args=["-y", "@mettamatt/code-reasoning@latest"],
        tool_prefix="code_reasoning",
        env={
            **os.environ,
            "LOG_LEVEL": "error",  # ログレベルをerrorに設定してinfoログを抑制
            "MCP_DEBUG": "false",  # MCPデバッグモードを無効化
            "NODE_OPTIONS": (
                os.environ.get("NODE_OPTIONS", "").strip()
                + f" --require {_make_code_reasoning_patch()}"
            ).strip(),
        },
    )
    return [filesystem_server, code_reasoning]

def build_agent(
    *,
    instructions_override: str | None = None,
    model: OpenAIChatModel | None = None,
    toolsets: list[MCPServerStdio] | None = None,
) -> Agent:
    return Agent(
        instructions=instructions_override or instructions,
        model=model or build_model(),
        toolsets=toolsets or build_toolsets(),
    )

async def main():
    agent = build_agent()
    async with agent:
        await agent.to_cli()

if __name__ == "__main__":
  asyncio.run(main())
