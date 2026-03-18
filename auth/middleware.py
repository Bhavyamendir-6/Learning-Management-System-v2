"""
auth/middleware.py — Flask request authentication decorator.

Usage:
    from ..auth import require_auth

    @app.route("/api/protected")
    @require_auth
    def my_view():
        user_id  = g.user_id   # user ID string from JWT
        username = g.username  # username claim from JWT
        ...
"""

from functools import wraps

from flask import g, request, jsonify

from .handler import decode_access_token, AuthError


def require_auth(f):
    """
    Flask route decorator that enforces JWT authentication.

    Reads the Authorization header:
        Authorization: Bearer <jwt_token>

    On success:
        - Sets  g.user_id   to the JWT 'sub' claim (user ID string)
        - Sets  g.username  to the JWT 'username' claim
        - Calls the wrapped view function

    On failure:
        Returns JSON  { "error": "<message>" }  with HTTP 401.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return jsonify({"error": "Authorization header is missing."}), 401

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify(
                {"error": "Authorization header must be: Bearer <token>"}
            ), 401

        token = parts[1].strip()
        if not token:
            return jsonify({"error": "Bearer token is empty."}), 401

        try:
            payload = decode_access_token(token)
        except AuthError as exc:
            return jsonify({"error": str(exc)}), exc.status_code

        # Inject verified identity into Flask's request context
        g.user_id = payload["sub"]  # user ID string
        g.username = payload["username"]

        return f(*args, **kwargs)

    return decorated
