"""Trending Insights Tool - retrieves trending community content."""

from typing import Annotated
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def get_trending_insights(
    limit: Annotated[int, "Number of trending items to return (recommended: 5)"],
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve the most upvoted community items (quizzes and flashcards).

    Args:
        limit: Maximum number of items to return

    Returns:
        dict: List of trending community content
    """
    limit = limit or 5

    try:
        from database.connection import get_session
        from database.repositories import CommunityRepository

        async with get_session() as session:
            repo = CommunityRepository(session)
            items = await repo.get_items(sort_by="popular", limit=limit)

        if not items:
            return {
                "status": "empty",
                "items": [],
                "message": "No community content found yet. Be the first to publish your quizzes and flashcards!",
            }

        return {
            "status": "success",
            "items": [
                {
                    "title": item.title,
                    "type": item.item_type,
                    "upvotes": item.upvotes,
                    "description": item.description or "",
                }
                for item in items
            ],
        }

    except Exception as e:
        return {"status": "error", "message": f"Error retrieving trending insights: {str(e)}"}
