from .config import GEMINI_MODEL_NAME
from dotenv import load_dotenv
from google.adk.agents import Agent
from .prompts import ROOT_AGENT_INSTRUCTION
from .subagents.pdf_handler import pdf_handler_agent
from .subagents.quiz_agent import quiz_agent
from .subagents.quiz_history_agent import quiz_history_agent
from .subagents.learning_content_agent import learning_content_agent
from .subagents.tutor_agent import tutor_agent
from .subagents.community_agent import community_agent

load_dotenv()


root_agent = Agent(
    name="LMS_Executive",
    model=GEMINI_MODEL_NAME,
    description="Root orchestrator that routes user requests to specialized sub-agents for PDF management, quizzes, tutoring, learning content, and community features.",
    instruction=ROOT_AGENT_INSTRUCTION,
    sub_agents=[
        pdf_handler_agent,
        quiz_agent,
        quiz_history_agent,
        learning_content_agent,
        tutor_agent,
        community_agent,
    ],
)
