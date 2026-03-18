from .config import GEMINI_MODEL_NAME
from dotenv import load_dotenv
from google.adk.agents import Agent
from .utils.callbacks import before_tool_callback
from .prompts import ROOT_AGENT_INSTRUCTION
from .subagents.pdf_handler import pdf_handler_agent
from .subagents.quiz_agent import quiz_agent
from .subagents.quiz_history_agent import quiz_history_agent
from .subagents.learning_content_agent import learning_content_agent
from .subagents.tutor_agent import tutor_agent
from .subagents.community_agent import community_agent

load_dotenv()


pdf_handler_agent.before_tool_callback = before_tool_callback


root_agent = Agent(
    name="LMS_Executive",
    model=GEMINI_MODEL_NAME,
    instruction=ROOT_AGENT_INSTRUCTION,
    before_tool_callback=before_tool_callback,
    sub_agents=[
        pdf_handler_agent,
        quiz_agent,
        quiz_history_agent,
        learning_content_agent,
        tutor_agent,
        community_agent,
    ],
)
