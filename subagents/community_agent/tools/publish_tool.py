import json
import uuid
from typing import Annotated
from database.connection import get_session
from database.repositories import CommunityRepository


async def publish_to_community(
    title: Annotated[
        str,
        "A short title describing the content to be published. E.g. 'Photosynthesis Flashcards'",
    ],
    description: Annotated[str, "A brief description of the content."] = "",
    tool_context=None,
) -> str:
    """
    Publishes the user's most recently generated flashcard set to the public community.
    It reads the 'last_generated_content' and 'last_generated_type' from the agent session state.
    """
    print(f"[publish_tool] title={title!r}, description={description!r}")
    print(f"[publish_tool] tool_context is None: {tool_context is None}")

    if tool_context:
        # Debug: dump all known state keys
        try:
            all_keys = (
                list(tool_context.state.keys())
                if hasattr(tool_context.state, "keys")
                else "state has no keys()"
            )
            print(f"[publish_tool] State keys: {all_keys}")
        except Exception as e:
            print(f"[publish_tool] Could not read state keys: {e}")

    # Verify user exists in the adk session state
    user_id_str = tool_context.state.get("current_user_id") if tool_context else None
    print(f"[publish_tool] current_user_id from state: {user_id_str!r}")
    if not user_id_str:
        return "Error: User ID not found in session state."

    # Look for the last generated content
    content_json = (
        tool_context.state.get("last_generated_content") if tool_context else None
    )
    item_type = tool_context.state.get("last_generated_type") if tool_context else None

    print(f"[publish_tool] item_type={item_type!r}")
    print(
        f"[publish_tool] content_json type={type(content_json).__name__}, is None={content_json is None}"
    )
    if content_json:
        preview = str(content_json)[:200]
        print(f"[publish_tool] content_json preview: {preview}")

    if not content_json or not item_type:
        return "You must generate flashcards first before you can publish anything to the community."

    # Ensure content_json is a JSON string (tools may store it as a dict)
    if isinstance(content_json, dict) or isinstance(content_json, list):
        content_json = json.dumps(content_json)
        print("[publish_tool] Converted content_json from dict/list to string")
    elif not isinstance(content_json, str):
        content_json = json.dumps(content_json)
        print(
            f"[publish_tool] Converted content_json from {type(content_json).__name__} to string"
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
        print(f"[publish_tool] user_uuid={user_uuid}")
        async with get_session() as db_session:
            repo = CommunityRepository(db_session)
            item = await repo.publish_item(
                author_id=user_uuid,
                item_type=item_type,
                title=title,
                content_json=content_json,
                description=description,
            )
            # Note: get_session() context manager auto-commits on clean exit
            print(f"[publish_tool] SUCCESS! Published item id={item.id}")

            # Clear the state so they don't double publish by accident
            if tool_context:
                try:
                    del tool_context.state["last_generated_content"]
                except (KeyError, Exception):
                    pass
                try:
                    del tool_context.state["last_generated_type"]
                except (KeyError, Exception):
                    pass

            return f"Successfully published {item_type} titled '{item.title}' to the global community."
    except Exception as e:
        import traceback

        print(f"[publish_tool] EXCEPTION: {e}")
        traceback.print_exc()
        return f"Error publishing to community: {str(e)}"
