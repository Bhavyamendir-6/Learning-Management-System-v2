from ...config import GEMINI_MODEL_NAME
from google.adk.agents import Agent
from .tools import publish_to_community
from .prompt import COMMUNITY_AGENT_PROMPT

community_agent = Agent(
    name="Community_Agent",
    model=GEMINI_MODEL_NAME,
    description="Handles interactions with the LMS community features. Transfer to this agent when the user wants to publish flashcards to the community.",
    instruction=COMMUNITY_AGENT_PROMPT,
    tools=[publish_to_community],
)
