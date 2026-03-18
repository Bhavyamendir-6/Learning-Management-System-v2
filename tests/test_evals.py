"""
ADK Evaluation Tests for LMS Project

Each test function evaluates a specific sub-agent or routing behavior
using pre-defined test fixtures and the AgentEvaluator from google-adk.

Run all:   python -m pytest tests/test_evals.py -v
Run one:   python -m pytest tests/test_evals.py::test_root_agent_routing -v
"""

import os
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

# Resolve paths relative to this file
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")

# The agent module path — parent directory of this tests/ folder
AGENT_MODULE = os.path.basename(os.path.dirname(TESTS_DIR))


# ──────────────────────────────────────────────────────────────────────
# Root Agent — Intent Routing
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_root_agent_routing():
    """Verify the root agent routes user intents to the correct sub-agent."""
    await AgentEvaluator.evaluate(
        agent_module=AGENT_MODULE,
        eval_dataset_file_path_or_dir=os.path.join(
            FIXTURES_DIR, "root_agent_routing.test.json"
        ),
    )


# ──────────────────────────────────────────────────────────────────────
# PDF Handler Agent
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_handler():
    """Verify the PDF handler agent uses list_files correctly."""
    await AgentEvaluator.evaluate(
        agent_module=AGENT_MODULE,
        eval_dataset_file_path_or_dir=os.path.join(
            FIXTURES_DIR, "pdf_handler.test.json"
        ),
    )


# ──────────────────────────────────────────────────────────────────────
# Quiz Master Agent
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_quiz_agent():
    """Verify the quiz agent uses generate_quiz correctly."""
    await AgentEvaluator.evaluate(
        agent_module=AGENT_MODULE,
        eval_dataset_file_path_or_dir=os.path.join(
            FIXTURES_DIR, "quiz_agent.test.json"
        ),
    )


# ──────────────────────────────────────────────────────────────────────
# Quiz Historian Agent
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_quiz_history_agent():
    """Verify the quiz history agent retrieves history and stats."""
    await AgentEvaluator.evaluate(
        agent_module=AGENT_MODULE,
        eval_dataset_file_path_or_dir=os.path.join(
            FIXTURES_DIR, "quiz_history_agent.test.json"
        ),
    )


# ──────────────────────────────────────────────────────────────────────
# Learning Content Agent
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_learning_content_agent():
    """Verify summarization and flashcard generation tools."""
    await AgentEvaluator.evaluate(
        agent_module=AGENT_MODULE,
        eval_dataset_file_path_or_dir=os.path.join(
            FIXTURES_DIR, "learning_content_agent.test.json"
        ),
    )


# ──────────────────────────────────────────────────────────────────────
# AI Tutor Agent
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tutor_agent():
    """Verify tutoring session start and learning notes retrieval."""
    await AgentEvaluator.evaluate(
        agent_module=AGENT_MODULE,
        eval_dataset_file_path_or_dir=os.path.join(
            FIXTURES_DIR, "tutor_agent.test.json"
        ),
    )


# ──────────────────────────────────────────────────────────────────────
# Community Agent
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_community_agent():
    """Verify community publishing tool usage."""
    await AgentEvaluator.evaluate(
        agent_module=AGENT_MODULE,
        eval_dataset_file_path_or_dir=os.path.join(
            FIXTURES_DIR, "community_agent.test.json"
        ),
    )
