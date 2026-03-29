// ─────────────────────────────────────────────────────────────────────────────
// Token helpers  (localStorage key: "lms_token")
// ─────────────────────────────────────────────────────────────────────────────

const TOKEN_KEY = "lms_token";

export function getToken(): string | null {
    if (typeof window !== "undefined") {
        return localStorage.getItem(TOKEN_KEY);
    }
    return null;
}

export function setToken(token: string): void {
    if (typeof window !== "undefined") {
        localStorage.setItem(TOKEN_KEY, token);
    }
}

export function clearToken(): void {
    if (typeof window !== "undefined") {
        localStorage.removeItem(TOKEN_KEY);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Core fetch wrapper
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001/api";

export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
    const token = getToken();
    const headers = new Headers(options.headers);

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    // Let the browser set the correct Content-Type (with boundary) for FormData
    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
    }

    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
        ...options,
        headers,
    });

    let data;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        data = await response.json();
    } else {
        data = await response.text();
    }

    if (!response.ok) {
        throw new Error(
            data?.detail || data?.message || (typeof data === "string" ? data : "An error occurred")
        );
    }

    return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// Community APIs
//   Backend:  GET  /api/community/items?item_type=...&sort_by=...
//             POST /api/community/items/:id/upvote
//             GET  /api/community/trending?limit=...
// ─────────────────────────────────────────────────────────────────────────────

export async function getCommunityItems(
    type?: "quiz" | "flashcard_set",
    sortBy: "recent" | "popular" = "popular"
) {
    const params = new URLSearchParams();
    if (type) params.append("item_type", type);
    params.append("sort_by", sortBy);
    return fetchAPI(`/community/items?${params.toString()}`);
}

export async function toggleItemUpvote(itemId: string) {
    return fetchAPI(`/community/items/${itemId}/upvote`, { method: "POST" });
}

// ─────────────────────────────────────────────────────────────────────────────
// Leaderboard APIs
//   Backend:  GET  /api/leaderboard
//             GET  /api/leaderboard/me
// ─────────────────────────────────────────────────────────────────────────────

export async function getLeaderboard() {
    return fetchAPI("/leaderboard");
}

export async function getMyRank() {
    return fetchAPI("/leaderboard/me");
}

// ─────────────────────────────────────────────────────────────────────────────
// Peer-Review APIs
//   Backend:  GET  /api/peer-reviews/pending
//             POST /api/peer-reviews/:review_id/grade
// ─────────────────────────────────────────────────────────────────────────────

export async function getPendingPeerReviews() {
    return fetchAPI("/peer-reviews/pending");
}

export async function submitPeerGrade(
    reviewId: string,
    score: number,
    feedback: string
) {
    return fetchAPI(`/peer-reviews/${reviewId}/grade`, {
        method: "POST",
        body: JSON.stringify({ score, feedback }),
    });
}
