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

openai_api_key = os.environ.get("OPENAI_API_KEY")

model = OpenAIChatModel("gpt-4o", provider=OpenAIProvider(api_key=openai_api_key))

instructions = """
あなたはコードベースの保守と開発を担当する専門エージェントとして振る舞ってください。
"""

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
        "NODE_OPTIONS": (os.environ.get("NODE_OPTIONS", "").strip() + f" --require {_make_code_reasoning_patch()}").strip(),
    },
)

agent = Agent(
    instructions=instructions,
    model=model,
    toolsets=[filesystem_server, code_reasoning],
)

async def main():
    async with agent:
        await agent.to_cli()

if __name__ == "__main__":
  asyncio.run(main())
