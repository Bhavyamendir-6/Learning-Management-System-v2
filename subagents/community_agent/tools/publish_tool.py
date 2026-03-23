import json
import logging
import uuid
from typing import Annotated
from google.adk.tools import ToolContext
from database.connection import get_session
from database.repositories import CommunityRepository

logger = logging.getLogger(__name__)


async def publish_to_community(
    title: Annotated[str, "A short title describing the content to be published. E.g. 'Photosynthesis Flashcards'"],
    description: Annotated[str, "A brief description of the content"],
    tool_context: ToolContext,
) -> dict:
    """
    Publishes the user's most recently generated flashcard set to the public community.
    It reads the 'last_generated_content' and 'last_generated_type' from the agent session state.

    Args:
        title: A short title for the content
        description: A brief description of the content

    Returns:
        dict: Publish result with status
    """
    logger.debug(
        "[publish_tool] title=%r description=%r context_present=%s",
        title,
        description,
        tool_context is not None,
    )

    try:
        all_keys = (
            list(tool_context.state.keys())
            if hasattr(tool_context.state, "keys")
            else "state has no keys()"
        )
        logger.debug("[publish_tool] state keys: %s", all_keys)
    except Exception as e:
        logger.warning("[publish_tool] could not read state keys: %s", e)

    # Verify user exists in the adk session state
    user_id_str = tool_context.state.get("current_user_id")
    logger.debug("[publish_tool] current_user_id=%r", user_id_str)
    if not user_id_str:
        return {"status": "error", "message": "User ID not found in session state."}

    # Look for the last generated content
    content_json = tool_context.state.get("last_generated_content")
    item_type = tool_context.state.get("last_generated_type")

    logger.debug(
        "[publish_tool] item_type=%r content_type=%s content_present=%s",
        item_type,
        type(content_json).__name__,
        content_json is not None,
    )
    if content_json:
        logger.debug("[publish_tool] content preview: %s", str(content_json)[:200])

    if not content_json or not item_type:
        return {"status": "error", "message": "You must generate flashcards first before you can publish anything to the community."}

    # Ensure content_json is a JSON string (tools may store it as a dict)
    if isinstance(content_json, (dict, list)):
        content_json = json.dumps(content_json)
        logger.debug("[publish_tool] converted content_json from dict/list to string")
    elif not isinstance(content_json, str):
        content_json = json.dumps(content_json)
        logger.debug(
            "[publish_tool] converted content_json from %s to string",
            type(content_json).__name__,
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
        async with get_session() as db_session:
            repo = CommunityRepository(db_session)
            item = await repo.publish_item(
                author_id=user_uuid,
                item_type=item_type,
                title=title,
                content_json=content_json,
                description=description,
            )
            logger.info(
                "[publish_tool] published item_id=%s type=%s title=%r",
                item.id,
                item_type,
                title,
            )

            # Clear the state so they don't double-publish by accident
            try:
                del tool_context.state["last_generated_content"]
            except KeyError:
                pass
            try:
                del tool_context.state["last_generated_type"]
            except KeyError:
                pass

            return {
                "status": "published",
                "item_id": str(item.id),
                "item_type": item_type,
                "title": item.title,
                "message": f"Successfully published {item_type} titled '{item.title}' to the global community.",
            }
    except Exception as e:
        logger.exception("[publish_tool] exception publishing item: %s", e)
        return {"status": "error", "message": f"Error publishing to community: {str(e)}"}
