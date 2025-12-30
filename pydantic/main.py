import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")

model = OpenAIChatModel("gpt-4o", provider=OpenAIProvider(api_key=openai_api_key))
agent = Agent(
    # instructions=instructions,
    model=model,
)

if __name__ == "__main__":
  agent.to_cli_sync()