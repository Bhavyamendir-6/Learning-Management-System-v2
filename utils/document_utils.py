"""Shared document-matching utilities used by quiz, tutor, and content tools."""


def normalize_doc_name(name: str) -> str:
    """Normalize a document name for fuzzy matching (lowercase, no .pdf extension)."""
    name = name.strip().lower()
    if name.endswith(".pdf"):
        name = name[:-4]
    return name


def find_document(documents, document_name: str):
    """
    Find a document in a list by fuzzy-matching its display_name.

    Returns:
        (doc, resolved_display_name) if found, or (None, original_name) if not.
    """
    normalized = normalize_doc_name(document_name)
    for doc in documents:
        display = getattr(doc, "display_name", None) or getattr(doc, "name", "")
        if display == document_name or normalize_doc_name(display) == normalized:
            return doc, display
    return None, document_name
