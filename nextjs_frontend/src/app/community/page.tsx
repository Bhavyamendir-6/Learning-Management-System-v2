"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import { getCommunityItems, toggleItemUpvote } from "../../lib/api";
import CommunityItemCard, { CommunityItem } from "../../components/CommunityItemCard";
import { useRouter } from "next/navigation";

export default function CommunityDashboard() {
    const router = useRouter();
    const [items, setItems] = useState<CommunityItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'all' | 'flashcard_set'>('all');
    const [sortBy, setSortBy] = useState<'recent' | 'popular'>('popular');

    // Sidebar state (mocked since we don't have full chat state here, just nav)
    const [user, setUser] = useState<{ username: string } | null>(null);

    useEffect(() => {
        // Load user from token/storage or API
        const token = localStorage.getItem("lms_token");
        if (!token) {
            router.push("/login");
            return;
        }
        // Ideally fetch /api/auth/me here
        fetch("http://localhost:5001/api/auth/me", {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(res => res.json())
            .then(data => setUser(data))
            .catch(() => router.push("/login"));
    }, [router]);

    useEffect(() => {
        const fetchItems = async () => {
            setLoading(true);
            try {
                // If 'all' is selected, we still explicitly request flashcard_set to avoid historic quizzes
                const typeToFetch = activeTab === 'all' ? 'flashcard_set' : activeTab;
                const res = await getCommunityItems(typeToFetch, sortBy);
                setItems(res.items || []);
            } catch (err) {
                console.error("Failed to load community items", err);
            } finally {
                setLoading(false);
            }
        };
        fetchItems();
    }, [activeTab, sortBy]);

    const handleUpvote = async (itemId: string) => {
        try {
            const res = await toggleItemUpvote(itemId);
            // Optimistic update
            setItems(prevItems => prevItems.map(item => {
                if (item.id === itemId) {
                    return { ...item, upvotes: item.upvotes + (res.upvoted ? 1 : -1) };
                }
                return item;
            }));
        } catch (err) {
            console.error("Failed to toggle upvote", err);
        }
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
                {/* Close button — top right */}
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
                    <div className="max-w-5xl mx-auto">
                        <header className="mb-14 text-center lg:text-left">
                            <h1 className="text-5xl font-extrabold tracking-tight mb-4" style={{ fontFamily: 'var(--font-serif)' }}>
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#1e3a5f] via-[#2c5282] to-[#c9a84c]">Community Hub</span>
                            </h1>
                            <p className="text-lg text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                                Discover and practice learning materials created by other students. Explore popular flashcard sets and master them together.
                            </p>
                        </header>

                        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
                            <div className="flex items-center p-1 bg-[#1e3a5f]/5 dark:bg-[#c9a84c]/5 backdrop-blur-md rounded-xl border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10">
                                {['all', 'flashcard_set'].map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab as any)}
                                        className={`px-5 py-2 text-sm font-bold rounded-lg transition-all capitalize ${activeTab === tab
                                            ? 'bg-white dark:bg-[#1e3a5f] text-[#1e3a5f] dark:text-white shadow-sm'
                                            : 'text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 hover:text-[#1e3a5f] dark:hover:text-[#e8e4db] hover:bg-white/50 dark:hover:bg-[#c9a84c]/5'
                                            }`}
                                    >
                                        {tab === 'flashcard_set' ? 'Flashcards' : tab}
                                    </button>
                                ))}
                            </div>

                            <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50">Sort by:</span>
                                <select
                                    value={sortBy}
                                    onChange={(e) => setSortBy(e.target.value as 'recent' | 'popular')}
                                    className="bg-white/50 dark:bg-[#0a1220]/50 border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 text-sm font-semibold rounded-xl px-4 py-2 outline-none focus:ring-2 focus:ring-[#c9a84c]/30 text-[#1e3a5f] dark:text-[#e8e4db]"
                                >
                                    <option value="popular">Most Popular 🔥</option>
                                    <option value="recent">Recently Added 🕒</option>
                                </select>
                            </div>
                        </div>

                        {loading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {[...Array(6)].map((_, i) => (
                                    <div key={i} className="h-48 bg-[#1e3a5f]/5 dark:bg-[#c9a84c]/5 rounded-2xl animate-pulse backdrop-blur-sm border border-[#1e3a5f]/5 dark:border-[#c9a84c]/5"></div>
                                ))}
                            </div>
                        ) : items.length === 0 ? (
                            <div className="py-20 text-center flex flex-col items-center justify-center bg-white/20 dark:bg-[#0f1a2b]/30 rounded-3xl border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 border-dashed">
                                <span className="text-6xl mb-4 opacity-50">📭</span>
                                <h3 className="text-xl font-bold text-[#1e3a5f] dark:text-[#e8e4db] mb-2">No community items found</h3>
                                <p className="text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50 max-w-sm">Be the first to publish a flashcard set to help others learn!</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-20">
                                {items.map(item => (
                                    <CommunityItemCard
                                        key={item.id}
                                        item={item}
                                        onUpvote={handleUpvote}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
