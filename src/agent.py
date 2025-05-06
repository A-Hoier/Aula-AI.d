from __future__ import annotations as _annotations

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic_ai import Agent, Tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import app_settings
from src.aula_client import AulaClient
from src.constants import AVAILABLE_AGENTS, AVAILABLE_MODELS
from src.llm import get_async_openai_client
from src.research_tool import (
    ResearchDependencies,
    SearchDataclass,
    fetch_url,
    get_search,
)

current_time = datetime.now().isoformat()
aula = AulaClient(app_settings().AULA_USER, app_settings().AULA_PWD.get_secret_value())


class ResearchResult(BaseModel):
    research_title: str = Field(
        description="This is a top level Markdown heading that covers the topic of the query and answer prefix it with #"
    )
    research_main: str = Field(
        description="This is a main section that provides answers for the query and research"
    )
    research_bullets: str = Field(
        description="This is a set of bulletpoints that summarize the answers for query"
    )


def create_agent(model: str, agent: str) -> Agent:
    """
    Create an agent with the given model name.
    Args:
        model_name (str): The name of the model to use.
    """
    if model not in AVAILABLE_MODELS:
        raise ValueError(f"Model {model} not in {AVAILABLE_MODELS}")
    if agent not in AVAILABLE_AGENTS:
        raise ValueError(f"Agent {agent} not in {AVAILABLE_AGENTS}")
    if not model.startswith("anthropic"):
        client = get_async_openai_client()
        model = OpenAIModel(model, provider=OpenAIProvider(openai_client=client))
    if agent == "research_agent":
        system_prompt = f"""current_time: {current_time}
You're a helpful research assistant, you are an expert in research 
        If you are given a question you write strong keywords to do 3-5 searches in total 
        (each with a query_number) and then combine the results. If some of the results seem relevant, 
        use the fetch_url tool to get the full content of the page.
"""
        tools = [
            Tool(
                name="google_search",
                description="Look up 3–5 results on Google.",
                function=get_search,
            ),
            Tool(
                name="fetch_url",
                description="Fetch and return the plain‐text of any URL.",
                function=fetch_url,
            ),
        ]
    elif agent == "aula_agent":
        system_prompt = f"""current_time: {current_time}
You're a helpful research assistant. You're an expert in navigating the danish school communication system, Aula.
Only use the tools if the user is talking about the school, institution or about their kids.
Make sure to set the active child before using any of the tools (except for fetch_basic_data).
"""
        tools = [
            Tool(
                name="set_active_child",
                description="Set which child profile we’re operating on. Expects a single string argument: the child's name.",
                function=aula.set_active_child,
            ),
            Tool(
                name="fetch_basic_data",
                description="Return some basic info on all children’s {name: institution}.",
                function=aula.fetch_basic_data,
            ),
            Tool(
                name="fetch_daily_overview",
                description="Return today’s presence overview for the active child. Requires active child to be set.",
                function=aula.fetch_daily_overview,
            ),
            Tool(
                name="fetch_messages",
                description="Fetch the latest unread message for the active child. Requires active child to be set.",
                function=aula.fetch_messages,
            ),
            Tool(
                name="fetch_calendar",
                description="Fetch upcoming calendar events for the next N days. Expects an integer argument. Requires active child to be set.",
                function=aula.fetch_calendar,
            ),
        ]

    return Agent(
        model=model,
        deps_type=ResearchDependencies,
        # output_type=ResearchResult,
        system_prompt=system_prompt,
        tools=tools,
    )


async def get_response(query: str, model: str, agent: str) -> str:
    from datetime import date

    current = date.today().isoformat()

    # pick your model at runtime:
    agent = create_agent(model, agent)

    # prepare your deps
    deps = SearchDataclass(max_results=3, todays_date=current)

    # run!
    result = await agent.run(query, deps=deps)
    return result.output
