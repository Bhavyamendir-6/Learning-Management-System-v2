"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import { getLeaderboard } from "../../lib/api";
import { useRouter } from "next/navigation";

interface LeaderboardEntry {
    rank: number;
    username: string;
    total_score: number;
    quizzes_completed: number;
}

interface MyRank {
    rank: number;
    username: string;
    total_score: number;
    quizzes_completed: number;
}

export default function LeaderboardPage() {
    const router = useRouter();
    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
    const [myRank, setMyRank] = useState<MyRank | null>(null);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<{ username: string } | null>(null);

    useEffect(() => {
        const token = localStorage.getItem("lms_token");
        if (!token) {
            router.push("/login");
            return;
        }
        fetch("http://localhost:5001/api/auth/me", {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then((data) => setUser(data))
            .catch(() => router.push("/login"));
    }, [router]);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const res = await getLeaderboard();
                setLeaderboard(res.leaderboard || []);
                setMyRank(res.my_rank || null);
            } catch (err) {
                console.error("Failed to load leaderboard", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const getMedalIcon = (rank: number) => {
        if (rank === 1) return "🥇";
        if (rank === 2) return "🥈";
        if (rank === 3) return "🥉";
        return `#${rank}`;
    };

    return (
        <main className="flex h-screen w-screen overflow-hidden bg-[var(--bg-color)] bg-center selection:bg-[#c9a84c]/30 text-[var(--text-color)]">
            {/* Ambient Backgrounds */}
            <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[#1e3a5f]/10 dark:bg-[#1e3a5f]/15 blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#c9a84c]/8 dark:bg-[#c9a84c]/10 blur-[120px] pointer-events-none" />
            <div className="absolute top-[20%] right-[20%] w-[30%] h-[30%] rounded-full bg-[#2c5282]/8 dark:bg-[#2c5282]/10 blur-[100px] pointer-events-none" />

            <Sidebar
                sessions={[]}
                activeSessionId={null}
                onSelectSession={() => { }}
                onNewSession={() => router.push("/")}
                onLogout={() => {
                    localStorage.removeItem("lms_token");
                    router.push("/login");
                }}
                user={user}
                onQuickAction={() => { }}
                onUpload={() => { }}
                isUploading={false}
                documents={[]}
            />

            <div className="flex-1 flex overflow-hidden relative z-0">
                {/* Close button */}
                <button
                    onClick={() => router.push("/")}
                    className="absolute top-5 right-5 z-50 w-10 h-10 flex items-center justify-center rounded-full bg-white/60 dark:bg-white/10 backdrop-blur-md border border-[#1e3a5f]/15 dark:border-[#c9a84c]/10 text-[#1e3a5f] dark:text-[#c8c3b8] hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/30 transition-all shadow-sm"
                    title="Back to Chat"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>

                <div className="flex-1 overflow-y-auto px-8 py-10 custom-scrollbar">
                    <div className="max-w-4xl mx-auto">
                        {/* Header */}
                        <header className="mb-14 text-center lg:text-left">
                            <h1
                                className="text-5xl font-extrabold tracking-tight mb-4"
                                style={{ fontFamily: "var(--font-serif)" }}
                            >
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c9a84c] via-[#d4af37] to-[#1e3a5f]">
                                    🏆 Leaderboard
                                </span>
                            </h1>
                            <p className="text-lg text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                                Top performers ranked by total quiz scores. Keep learning and climb the ranks!
                            </p>
                        </header>

                        {/* Your Position Card */}
                        {myRank && (
                            <div className="mb-10 p-6 rounded-2xl bg-gradient-to-r from-[#1e3a5f]/10 via-[#2c5282]/8 to-[#c9a84c]/10 dark:from-[#1e3a5f]/20 dark:via-[#2c5282]/15 dark:to-[#c9a84c]/15 border border-[#c9a84c]/20 dark:border-[#c9a84c]/25 backdrop-blur-md shadow-[0_0_30px_rgba(201,168,76,0.08)]">
                                <div className="flex items-center justify-between flex-wrap gap-4">
                                    <div className="flex items-center gap-4">
                                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#1e3a5f] to-[#2c5282] flex items-center justify-center text-white font-black text-xl shadow-lg ring-2 ring-[#c9a84c]/30">
                                            {myRank.rank <= 3 ? getMedalIcon(myRank.rank) : `#${myRank.rank}`}
                                        </div>
                                        <div>
                                            <p className="text-xs font-bold text-[#c9a84c] dark:text-[#c9a84c] uppercase tracking-[0.15em]">
                                                Your Position
                                            </p>
                                            <p className="text-2xl font-extrabold text-[#1e3a5f] dark:text-[#e8e4db]">
                                                Rank #{myRank.rank}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex gap-8">
                                        <div className="text-center">
                                            <p className="text-3xl font-black text-[#1e3a5f] dark:text-[#c9a84c]">
                                                {myRank.total_score}
                                            </p>
                                            <p className="text-xs font-semibold text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50 uppercase tracking-wide">
                                                Total Score
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-3xl font-black text-[#1e3a5f] dark:text-[#c9a84c]">
                                                {myRank.quizzes_completed}
                                            </p>
                                            <p className="text-xs font-semibold text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50 uppercase tracking-wide">
                                                Quizzes
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {!loading && !myRank && (
                            <div className="mb-10 p-6 rounded-2xl bg-[#1e3a5f]/5 dark:bg-[#c9a84c]/5 border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 border-dashed text-center">
                                <p className="text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 font-semibold">
                                    You haven&apos;t completed any quizzes yet. Take a quiz to appear on the leaderboard! 🎯
                                </p>
                            </div>
                        )}

                        {/* Leaderboard Table */}
                        <div className="bg-white/40 dark:bg-[#0f1a2b]/40 backdrop-blur-xl rounded-2xl border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 overflow-hidden shadow-[0_0_40px_rgba(30,58,95,0.05)] dark:shadow-[0_0_40px_rgba(201,168,76,0.05)]">
                            {/* Table Header */}
                            <div className="grid grid-cols-[60px_1fr_120px_120px] md:grid-cols-[80px_1fr_150px_150px] px-6 py-4 bg-[#1e3a5f]/5 dark:bg-[#c9a84c]/5 border-b border-[#1e3a5f]/10 dark:border-[#c9a84c]/10">
                                <span className="text-xs font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/80 uppercase tracking-[0.15em]">
                                    Rank
                                </span>
                                <span className="text-xs font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/80 uppercase tracking-[0.15em]">
                                    Student
                                </span>
                                <span className="text-xs font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/80 uppercase tracking-[0.15em] text-center">
                                    Score
                                </span>
                                <span className="text-xs font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/80 uppercase tracking-[0.15em] text-center">
                                    Quizzes
                                </span>
                            </div>

                            {/* Rows */}
                            {loading ? (
                                <div className="divide-y divide-[#1e3a5f]/5 dark:divide-[#c9a84c]/5">
                                    {[...Array(5)].map((_, i) => (
                                        <div
                                            key={i}
                                            className="grid grid-cols-[60px_1fr_120px_120px] md:grid-cols-[80px_1fr_150px_150px] px-6 py-5"
                                        >
                                            <div className="w-8 h-5 bg-[#1e3a5f]/10 dark:bg-[#c9a84c]/10 rounded animate-pulse" />
                                            <div className="w-32 h-5 bg-[#1e3a5f]/10 dark:bg-[#c9a84c]/10 rounded animate-pulse" />
                                            <div className="w-12 h-5 bg-[#1e3a5f]/10 dark:bg-[#c9a84c]/10 rounded animate-pulse mx-auto" />
                                            <div className="w-12 h-5 bg-[#1e3a5f]/10 dark:bg-[#c9a84c]/10 rounded animate-pulse mx-auto" />
                                        </div>
                                    ))}
                                </div>
                            ) : leaderboard.length === 0 ? (
                                <div className="py-20 text-center flex flex-col items-center justify-center">
                                    <span className="text-6xl mb-4 opacity-50">📊</span>
                                    <h3 className="text-xl font-bold text-[#1e3a5f] dark:text-[#e8e4db] mb-2">
                                        No leaderboard data yet
                                    </h3>
                                    <p className="text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50 max-w-sm">
                                        Complete quizzes to be the first on the leaderboard!
                                    </p>
                                </div>
                            ) : (
                                <div className="divide-y divide-[#1e3a5f]/5 dark:divide-[#c9a84c]/5">
                                    {leaderboard.map((entry) => {
                                        const isCurrentUser =
                                            user && entry.username === user.username;
                                        return (
                                            <div
                                                key={entry.rank}
                                                className={`grid grid-cols-[60px_1fr_120px_120px] md:grid-cols-[80px_1fr_150px_150px] px-6 py-4 items-center transition-all hover:bg-[#1e3a5f]/3 dark:hover:bg-[#c9a84c]/3 ${isCurrentUser
                                                        ? "bg-[#c9a84c]/5 dark:bg-[#c9a84c]/8 ring-1 ring-inset ring-[#c9a84c]/20"
                                                        : ""
                                                    } ${entry.rank <= 3 ? "py-5" : ""}`}
                                            >
                                                {/* Rank */}
                                                <div className="flex items-center">
                                                    {entry.rank <= 3 ? (
                                                        <span
                                                            className={`text-2xl ${entry.rank === 1
                                                                    ? "drop-shadow-[0_0_8px_rgba(255,215,0,0.5)]"
                                                                    : ""
                                                                }`}
                                                        >
                                                            {getMedalIcon(entry.rank)}
                                                        </span>
                                                    ) : (
                                                        <span className="text-lg font-bold text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 ml-1">
                                                            {entry.rank}
                                                        </span>
                                                    )}
                                                </div>

                                                {/* Username */}
                                                <div className="flex items-center gap-3 overflow-hidden">
                                                    <div
                                                        className={`w-9 h-9 shrink-0 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-md ${entry.rank === 1
                                                                ? "bg-gradient-to-br from-[#c9a84c] to-[#d4af37] ring-2 ring-[#c9a84c]/40"
                                                                : entry.rank === 2
                                                                    ? "bg-gradient-to-br from-[#a0aec0] to-[#718096] ring-2 ring-[#a0aec0]/30"
                                                                    : entry.rank === 3
                                                                        ? "bg-gradient-to-br from-[#c17c3b] to-[#a0522d] ring-2 ring-[#c17c3b]/30"
                                                                        : "bg-gradient-to-br from-[#1e3a5f] to-[#2c5282]"
                                                            }`}
                                                    >
                                                        {entry.username[0]?.toUpperCase() || "U"}
                                                    </div>
                                                    <span
                                                        className={`font-bold truncate ${isCurrentUser
                                                                ? "text-[#c9a84c] dark:text-[#c9a84c]"
                                                                : "text-[#1e3a5f] dark:text-[#e8e4db]"
                                                            } ${entry.rank <= 3 ? "text-base" : "text-sm"}`}
                                                    >
                                                        {entry.username}
                                                        {isCurrentUser && (
                                                            <span className="ml-2 text-xs font-semibold text-[#c9a84c]/80 bg-[#c9a84c]/10 px-2 py-0.5 rounded-full">
                                                                You
                                                            </span>
                                                        )}
                                                    </span>
                                                </div>

                                                {/* Score */}
                                                <div className="text-center">
                                                    <span
                                                        className={`font-black ${entry.rank <= 3
                                                                ? "text-xl text-[#c9a84c]"
                                                                : "text-base text-[#1e3a5f] dark:text-[#e8e4db]"
                                                            }`}
                                                    >
                                                        {entry.total_score}
                                                    </span>
                                                </div>

                                                {/* Quizzes */}
                                                <div className="text-center">
                                                    <span className="text-sm font-semibold text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 bg-[#1e3a5f]/5 dark:bg-[#c9a84c]/5 px-3 py-1 rounded-full">
                                                        {entry.quizzes_completed}
                                                    </span>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>

                        {/* Bottom spacing */}
                        <div className="h-20" />
                    </div>
                </div>
            </div>
        </main>
    );
}
