"""Document Stats Tool - retrieves per-document quiz performance statistics."""

from typing import Annotated, Optional
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def document_stats(
    document_name: Annotated[Optional[str], "The document to get stats for. Leave blank to get stats for all documents."],
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve quiz performance statistics for a specific document or all documents.

    Args:
        document_name: Name of the document (or None for all)

    Returns:
        dict: Statistics including attempts, scores, and trends
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        from Tools.db_handler import get_quiz_history
        from collections import defaultdict

        sessions = await get_quiz_history(user_id=user_id, limit=50)

        if not sessions:
            return {"status": "no_history", "stats": {}, "message": "No quiz history found. Take a quiz to see your statistics!"}

        # Group by document
        doc_stats: dict = defaultdict(lambda: {"attempts": 0, "scores": [], "best": 0, "latest": ""})

        for s in sessions:
            if s.get("status") != "completed":
                continue
            doc = s.get("document_name", "Unknown")
            if document_name and doc != document_name:
                continue
            final = s.get("final_score") or 0
            total = s.get("total_questions") or 5
            pct = round((final / total) * 100) if total > 0 else 0
            doc_stats[doc]["attempts"] += 1
            doc_stats[doc]["scores"].append(pct)
            doc_stats[doc]["best"] = max(doc_stats[doc]["best"], pct)
            doc_stats[doc]["latest"] = (s.get("started_at") or "")[:10]

        if not doc_stats:
            msg = "No completed quiz sessions found"
            if document_name:
                msg += f" for '{document_name}'"
            return {"status": "no_completed", "stats": {}, "message": msg + "."}

        stats_result = {}
        for doc, stat in doc_stats.items():
            scores = stat["scores"]
            avg = round(sum(scores) / len(scores)) if scores else 0
            stats_result[doc] = {
                "attempts": stat["attempts"],
                "average_score": avg,
                "best_score": stat["best"],
                "latest_attempt": stat["latest"],
            }

        return {"status": "success", "stats": stats_result}

    except Exception as e:
        return {"status": "error", "message": f"Error retrieving document stats: {str(e)}"}
