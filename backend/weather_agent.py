import asyncio
from dataclasses import dataclass
from typing import Any
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from lib.llm import openai


@dataclass
class Deps:
    city: str
    country: str


model = OpenAIModel("gpt-4o", openai_client=asyncio.run(openai.get_async_client()))
weather_agent = Agent(
    model=model,
    system_prompt=(
        "Be concise, reply with one sentence."
        "Make sure to get the country and city from the user, "
        "then use the `get_weather` tool to get the weather."
    ),
)


@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], city: str, country: str) -> dict[str, Any]:
    """Get the weather at a location."""
    print(f"Getting weather for {city}, {country}")
    print(ctx)
    return {
        "temperature": "25°C",
        "description": "Sunny with a chance of rain",
    }


async def main():
    result = await weather_agent.run("Hows the weather in Denmark, Copenhagen?")
    print(result.data)


asyncio.run(main())
