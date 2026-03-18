"use client";

import React, { useState } from "react";
import Link from "next/link";

interface SidebarProps {
    sessions: { session_id: string; created_at: number }[];
    activeSessionId: string | null;
    onSelectSession: (id: string) => void;
    onNewSession: () => void;
    onLogout: () => void;
    user: { username: string } | null;
    onQuickAction: (prompt: string) => void;
    onUpload: (file: File) => void;
    isUploading: boolean;
    documents?: { id: string; filename: string; uploaded_at: string }[];
}

const QUICK_ACTIONS = [
    { label: "Summarize", prompt: "Summarize my uploaded document", icon: "📄" },
    { label: "Quiz Me", prompt: "Quiz me with 5 questions on my document", icon: "🧠" },
    { label: "Flashcards", prompt: "Make 10 flashcards from my document", icon: "📇" },
    { label: "Tutor Me", prompt: "Tutor me on the main topic", icon: "👨‍🏫" },
    { label: "My Stats", prompt: "Show my document stats", icon: "📊" }
];

const SidebarDivider = () => (
    <div className="w-full flex justify-center py-2 shrink-0">
        <div className="w-[85%] h-px bg-gradient-to-r from-transparent via-[#c9a84c]/30 to-transparent shadow-[0_0_8px_rgba(201,168,76,0.2)]"></div>
    </div>
);

export default function Sidebar({
    sessions,
    activeSessionId,
    onSelectSession,
    onNewSession,
    onLogout,
    user,
    onQuickAction,
    onUpload,
    isUploading,
    documents = [],
}: SidebarProps) {
    const [isMinimized, setIsMinimized] = useState(false);

    const [width, setWidth] = useState(288); // 288px = w-72 default
    const [isResizing, setIsResizing] = useState(false);

    // Resize functionality
    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    };

    React.useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            // Set min width to 200px and max width to 600px
            const newWidth = Math.min(Math.max(200, e.clientX), 600);
            setWidth(newWidth);
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing]);

    if (isMinimized) {
        return (
            <aside className="w-20 glass h-full flex flex-col border-r border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 sticky top-0 z-10 animate-fade-in items-center py-6 bg-white/80 dark:bg-[#0f1a2b]/80 backdrop-blur-xl">
                <button
                    onClick={() => setIsMinimized(false)}
                    className="p-3 mb-6 rounded-xl bg-white/80 hover:bg-white dark:bg-white/5 dark:hover:bg-white/10 border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 hover:border-[#1e3a5f]/20 dark:hover:border-[#c9a84c]/20 transition-all group backdrop-blur-md shadow-[0_0_15px_rgba(0,0,0,0.05)] dark:shadow-[0_0_15px_rgba(0,0,0,0.2)] hover:shadow-[0_0_20px_rgba(201,168,76,0.2)] active:scale-95"
                    title="Expand Sidebar"
                >
                    <svg className="w-5 h-5 text-[#1e3a5f] dark:text-[#c9a84c] group-hover:text-[#c9a84c] dark:group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                </button>
                <button
                    onClick={onNewSession}
                    className="p-3 mb-6 rounded-xl bg-[#1e3a5f]/10 hover:bg-[#1e3a5f]/20 dark:bg-[#c9a84c]/15 dark:hover:bg-[#c9a84c]/25 border border-[#1e3a5f]/20 hover:border-[#1e3a5f]/40 dark:border-[#c9a84c]/20 dark:hover:border-[#c9a84c]/40 transition-all group backdrop-blur-md shadow-[0_0_15px_rgba(30,58,95,0.1)] active:scale-95"
                    title="New Chat"
                >
                    <svg className="w-5 h-5 text-[#1e3a5f] group-hover:text-[#1e3a5f] dark:text-[#c9a84c] dark:group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                    </svg>
                </button>

                <SidebarDivider />

                {/* Quick Actions icons only */}
                <div className="flex flex-col gap-4 mt-2 w-full px-4">
                    {QUICK_ACTIONS.map((action, idx) => (
                        <button
                            key={idx}
                            onClick={() => onQuickAction(action.prompt)}
                            className="w-full flex justify-center p-3 rounded-xl transition-all bg-[#1e3a5f]/5 hover:bg-[#1e3a5f]/15 dark:bg-[#c9a84c]/5 dark:hover:bg-[#c9a84c]/15 border border-[#1e3a5f]/5 dark:border-[#c9a84c]/10 hover:border-[#1e3a5f]/20 dark:hover:border-[#c9a84c]/25 shadow-[0_0_10px_rgba(30,58,95,0.03)] active:scale-95 group"
                            title={action.label}
                        >
                            <span className="text-xl opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all">{action.icon}</span>
                        </button>
                    ))}
                </div>

                <div className="mt-auto px-4 w-full flex flex-col gap-5 items-center">
                    <input
                        type="file"
                        accept="application/pdf"
                        className="hidden"
                        id="sidebar-pdf-upload-min"
                        onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                                onUpload(e.target.files[0]);
                                e.target.value = '';
                            }
                        }}
                    />
                    <label
                        htmlFor="sidebar-pdf-upload-min"
                        className={`w-full flex justify-center p-3 rounded-xl transition-all cursor-pointer ${isUploading
                            ? "bg-slate-200 dark:bg-slate-800 border-slate-300 dark:border-slate-700 opacity-70"
                            : "bg-[#1e3a5f]/10 hover:bg-[#1e3a5f]/20 dark:bg-[#c9a84c]/10 dark:hover:bg-[#c9a84c]/20 border border-[#1e3a5f]/20 dark:border-[#c9a84c]/20 shadow-lg active:scale-95 group"
                            }`}
                        title="Upload PDF"
                    >
                        {isUploading ? (
                            <div className="w-5 h-5 border-2 border-slate-400 border-t-[#1e3a5f] dark:border-t-[#c9a84c] rounded-full animate-spin"></div>
                        ) : (
                            <svg className="w-5 h-5 text-[#1e3a5f] group-hover:text-[#1e3a5f] dark:text-[#c9a84c] dark:group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                            </svg>
                        )}
                    </label>

                    <button
                        onClick={onLogout}
                        className="p-3 w-full flex justify-center text-rose-400/80 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-all border border-transparent hover:border-rose-500/20"
                        title="Logout"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                    </button>

                    <div className="w-10 h-10 mb-2 rounded-xl bg-gradient-to-br from-[#1e3a5f] to-[#2c5282] flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(30,58,95,0.3)] ring-2 ring-[#c9a84c]/20 shrink-0" title={user?.username || "Guest"}>
                        {user?.username?.[0]?.toUpperCase() || "U"}
                    </div>
                </div>
            </aside>
        );
    }

    return (
        <aside
            className="glass h-full flex flex-col border-r border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 sticky top-0 z-10 animate-fade-in relative transition-all duration-300 ease-in-out origin-left bg-white/50 dark:bg-transparent shrink-0"
            style={{ width: `${width}px`, transition: isResizing ? 'none' : 'width 0.3s ease-in-out' }}
        >
            {/* Header */}
            <div className="p-6 flex items-center justify-between relative overflow-hidden shrink-0">
                {/* Subtle glowing orb in the header */}
                <div className="absolute -top-10 -left-10 w-32 h-32 bg-[#c9a84c]/8 rounded-full blur-3xl"></div>

                <div className="flex items-center gap-3 relative z-10 overflow-hidden">
                    <button
                        onClick={() => setIsMinimized(true)}
                        className="p-2 -ml-2 rounded-lg text-[#1e3a5f] hover:text-[#1e3a5f] hover:bg-[#1e3a5f]/10 dark:text-[#c9a84c]/70 dark:hover:text-[#c9a84c] dark:hover:bg-[#c9a84c]/10 transition-colors shrink-0"
                        title="Minimize Sidebar"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                        </svg>
                    </button>
                    <h2 className="text-xl font-black bg-gradient-to-r from-[#1e3a5f] via-[#2c5282] to-[#1e3a5f] dark:from-[#c9a84c] dark:via-[#d4af37] dark:to-[#c9a84c] bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(30,58,95,0.2)] tracking-tight truncate" style={{ fontFamily: 'var(--font-serif)' }}>
                        LMS Agent
                    </h2>
                </div>
                <button
                    onClick={onNewSession}
                    className="p-2.5 rounded-xl bg-white hover:bg-[#faf9f6] dark:bg-white/5 dark:hover:bg-white/10 border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 hover:border-[#1e3a5f]/20 dark:hover:border-[#c9a84c]/25 transition-all group backdrop-blur-md shadow-[0_0_15px_rgba(0,0,0,0.05)] dark:shadow-[0_0_15px_rgba(0,0,0,0.2)] hover:shadow-[0_0_20px_rgba(201,168,76,0.15)] dark:hover:shadow-[0_0_20px_rgba(201,168,76,0.2)] active:scale-95 shrink-0"
                    title="New Chat"
                >
                    <svg
                        className="w-5 h-5 text-[#1e3a5f] group-hover:text-[#1e3a5f] dark:text-[#c9a84c] dark:group-hover:text-white transition-colors"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                    </svg>
                </button>
            </div>

            <SidebarDivider />

            {/* Scrollable Middle Section */}
            <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
                {/* Quick Actions */}
                <div className="py-3 px-4 space-y-2 relative shrink-0">
                    <h3 className="text-[10px] font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/60 uppercase tracking-[0.2em] mb-4 px-2 truncate">
                        Quick Actions
                    </h3>
                    <div className="flex flex-col gap-2">
                        {QUICK_ACTIONS.map((action, idx) => (
                            <button
                                key={idx}
                                onClick={() => onQuickAction(action.prompt)}
                                className="w-full text-left px-4 py-2.5 rounded-xl transition-all text-sm font-semibold text-[#1e3a5f] dark:text-[#c9a84c]/80 bg-[#1e3a5f]/5 hover:bg-[#1e3a5f]/10 dark:bg-[#c9a84c]/5 dark:hover:bg-[#c9a84c]/10 hover:text-[#1e3a5f] dark:hover:text-[#c9a84c] border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 hover:border-[#1e3a5f]/25 dark:hover:border-[#c9a84c]/25 shadow-[0_0_10px_rgba(30,58,95,0.03)] hover:shadow-[0_0_15px_rgba(201,168,76,0.08)] active:scale-[0.98] group flex items-center gap-3"
                            >
                                <span className="text-base opacity-90 group-hover:opacity-100 group-hover:scale-110 transition-all shrink-0">{action.icon}</span>
                                <span className="truncate">{action.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                <SidebarDivider />

                {/* Navigation */}
                <div className="py-2 px-4 space-y-2 relative shrink-0">
                    <h3 className="text-[10px] font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/60 uppercase tracking-[0.2em] mb-4 px-2 truncate">
                        Discover
                    </h3>
                    <Link href="/community" className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all text-sm font-semibold text-[#1e3a5f] dark:text-[#c8c3b8] hover:bg-[#1e3a5f]/5 dark:hover:bg-[#c9a84c]/5 border border-transparent hover:border-[#1e3a5f]/10 dark:hover:border-[#c9a84c]/10 group">
                        <span className="text-base group-hover:scale-110 transition-transform">🌍</span>
                        Community Hub
                    </Link>
                    <Link href="/leaderboard" className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all text-sm font-semibold text-[#1e3a5f] dark:text-[#c8c3b8] hover:bg-[#1e3a5f]/5 dark:hover:bg-[#c9a84c]/5 border border-transparent hover:border-[#1e3a5f]/10 dark:hover:border-[#c9a84c]/10 group">
                        <span className="text-base group-hover:scale-110 transition-transform">🏆</span>
                        Leaderboard
                    </Link>

                </div>

                <SidebarDivider />

                {/* History */}
                <div className="py-2 px-4 space-y-2 relative shrink-0">
                    <h3 className="text-[10px] font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/60 uppercase tracking-[0.2em] mb-4 px-2 truncate">
                        Chat History
                    </h3>
                    {sessions.map((s) => (
                        <button
                            key={s.session_id}
                            onClick={() => onSelectSession(s.session_id)}
                            className={`w-full text-left px-4 py-3 rounded-xl transition-all text-sm font-medium border ${activeSessionId === s.session_id
                                ? "bg-gradient-to-r from-[#1e3a5f]/8 dark:from-[#c9a84c]/10 to-[#c9a84c]/5 dark:to-[#c9a84c]/5 text-[#1e3a5f] dark:text-[#c9a84c] border-[#c9a84c]/20 dark:border-[#c9a84c]/25 shadow-[0_0_15px_rgba(201,168,76,0.06)] dark:shadow-[0_0_15px_rgba(201,168,76,0.1)]"
                                : "text-[#1e3a5f] hover:text-[#1e3a5f] dark:text-[#c8c3b8]/70 dark:hover:text-[#c8c3b8] border-transparent hover:bg-[#1e3a5f]/5 dark:hover:bg-[#c9a84c]/5 hover:border-[#1e3a5f]/10 dark:hover:border-[#c9a84c]/10"
                                }`}
                        >
                            <div className="flex items-center space-x-3">
                                {/* Decorative dot for active or inactive sessions */}
                                <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${activeSessionId === s.session_id
                                    ? "bg-[#c9a84c] shadow-[0_0_8px_rgba(201,168,76,0.6)]"
                                    : "bg-[#1e3a5f]/30 dark:bg-[#c8c3b8]/30"
                                    }`}></div>
                                <div className="truncate">
                                    Chat from {new Date(s.created_at * 1000).toLocaleDateString()}
                                </div>
                            </div>
                        </button>
                    ))}
                    {sessions.length === 0 && (
                        <div className="text-sm font-medium text-[#1e3a5f]/50 dark:text-[#c8c3b8]/40 text-center mt-8">
                            No sessions yet
                        </div>
                    )}
                </div>

                <SidebarDivider />

                {/* Upload PDF Section */}
                <div className="p-4 bg-[#1e3a5f]/3 dark:bg-[#c9a84c]/3 shrink-0">
                    <h3 className="text-[10px] font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/60 uppercase tracking-[0.2em] mb-3 px-2 truncate">
                        Upload Document
                    </h3>
                    <div className="px-2">
                        <input
                            type="file"
                            accept="application/pdf"
                            className="hidden"
                            id="sidebar-pdf-upload"
                            onChange={(e) => {
                                if (e.target.files && e.target.files[0]) {
                                    onUpload(e.target.files[0]);
                                    e.target.value = ''; // Reset input
                                }
                            }}
                        />
                        <label
                            htmlFor="sidebar-pdf-upload"
                            className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl transition-all text-sm font-semibold cursor-pointer ${isUploading
                                ? "bg-slate-200 dark:bg-slate-800 text-[#1e3a5f] dark:text-[#c8c3b8]/50 border border-slate-300 dark:border-slate-700 opacity-70"
                                : "bg-[#1e3a5f]/8 hover:bg-[#1e3a5f]/15 dark:bg-[#c9a84c]/8 dark:hover:bg-[#c9a84c]/15 text-[#1e3a5f] dark:text-[#c9a84c] border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 hover:border-[#1e3a5f]/30 dark:hover:border-[#c9a84c]/30 shadow-[0_0_10px_rgba(30,58,95,0.03)] hover:shadow-[0_0_15px_rgba(201,168,76,0.08)] active:scale-[0.98]"
                                }`}
                        >
                            {isUploading ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-slate-400 border-t-[#1e3a5f] dark:border-t-[#c9a84c] rounded-full animate-spin shrink-0"></div>
                                    <span className="truncate">Uploading...</span>
                                </>
                            ) : (
                                <>
                                    <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                    </svg>
                                    <span className="truncate">Upload PDF</span>
                                </>
                            )}
                        </label>
                    </div>
                </div>

                {/* Uploaded Documents List */}
                <SidebarDivider />
                <div className="py-2 px-4 space-y-2 relative shrink-0 pb-4">
                    <h3 className="text-[10px] font-extrabold text-[#1e3a5f] dark:text-[#c9a84c]/60 uppercase tracking-[0.2em] mb-4 px-2 truncate">
                        Uploaded Documents
                    </h3>
                    {documents.length > 0 ? documents.map((doc) => (
                        <div
                            key={doc.id}
                            className="w-full text-left px-4 py-2.5 rounded-xl transition-all text-sm font-medium border text-[#1e3a5f] hover:text-[#1e3a5f] dark:text-[#c8c3b8]/70 dark:hover:text-[#c8c3b8] border-transparent hover:bg-[#1e3a5f]/5 dark:hover:bg-[#c9a84c]/5 hover:border-[#1e3a5f]/10 dark:hover:border-[#c9a84c]/10 flex items-center gap-3"
                            title={doc.filename}
                        >
                            <svg className="w-4 h-4 shrink-0 text-[#c9a84c]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                            <span className="truncate flex-1">{doc.filename}</span>
                        </div>
                    )) : (
                        <div className="text-sm font-medium text-[#1e3a5f]/50 dark:text-[#c8c3b8]/40 text-center mt-2">
                            No documents yet
                        </div>
                    )}
                </div>
            </div>

            <SidebarDivider />

            {/* User Section */}
            <div className="p-5 bg-[#1e3a5f]/3 dark:bg-[#0a1220]/50 backdrop-blur-md relative overflow-hidden shrink-0">
                <div className="flex items-center justify-between relative z-10 w-full gap-2">
                    <div className="flex items-center space-x-3 overflow-hidden">
                        <div className="w-9 h-9 shrink-0 rounded-xl bg-gradient-to-br from-[#1e3a5f] to-[#2c5282] flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(30,58,95,0.15)] dark:shadow-[0_0_15px_rgba(30,58,95,0.3)] ring-2 ring-[#c9a84c]/20 dark:ring-[#c9a84c]/20">
                            {user?.username?.[0]?.toUpperCase() || "U"}
                        </div>
                        <span className="text-sm font-semibold truncate text-[#1e3a5f] dark:text-[#e8e4db]">
                            {user?.username || "Guest"}
                        </span>
                    </div>
                    <button
                        onClick={onLogout}
                        className="p-2 text-rose-400/80 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all shrink-0"
                        title="Logout"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Resize Handle */}
            <div
                className="absolute right-0 top-0 w-1.5 h-full cursor-col-resize hover:bg-[#c9a84c]/40 transition-colors z-50 flex items-center justify-center group"
                onMouseDown={handleMouseDown}
            >
                {/* Visual indicator on hover */}
                <div className="h-8 w-1 rounded-full bg-[#1e3a5f]/15 dark:bg-[#c9a84c]/20 group-hover:bg-[#c9a84c] dark:group-hover:bg-[#c9a84c] transition-colors pointer-events-none"></div>
            </div>
        </aside>
    );
}
