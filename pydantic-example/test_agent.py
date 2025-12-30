import asyncio
import os
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

filesystem_server = MCPServerStdio(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
    env={
        **os.environ,
        "LOG_LEVEL": "error",
    },
)

agent = Agent(
    instructions=instructions,
    model=model,
    toolsets=[filesystem_server],
)

async def main():
    async with agent:
        # 簡単なテスト：カレントディレクトリのファイル一覧を取得
        result = await agent.run("カレントディレクトリにあるPythonファイルを教えてください")
        print("テスト結果:")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
