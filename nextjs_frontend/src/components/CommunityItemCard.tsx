"use client";

import React, { useState, useMemo } from 'react';
import CommunityFlashcardViewer from './CommunityFlashcardViewer';

export interface CommunityItem {
    id: string;
    author_id: string;
    item_type: 'flashcard_set';
    title: string;
    description: string | null;
    content_json: string;
    upvotes: number;
    created_at: string;
}

interface Props {
    item: CommunityItem;
    onUpvote: (id: string) => void;
}

export default function CommunityItemCard({ item, onUpvote }: Props) {
    const [expanded, setExpanded] = useState(false);

    // Parse flashcards from content_json
    const flashcards = useMemo(() => {
        if (item.item_type !== 'flashcard_set') return [];
        try {
            let content = item.content_json;
            if (typeof content === 'string') {
                content = JSON.parse(content);
            }
            const obj = content as any;
            return obj?.flashcards || [];
        } catch {
            return [];
        }
    }, [item.content_json, item.item_type]);

    const isFlashcardSet = item.item_type === 'flashcard_set' && flashcards.length > 0;

    return (
        <div className={`bg-white/60 dark:bg-[#162236]/60 backdrop-blur-2xl border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 rounded-3xl p-6 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 flex flex-col group ${expanded ? 'col-span-1 md:col-span-2 lg:col-span-3 ring-2 ring-[#c9a84c]/40' : ''}`}>

            {/* Header: Icon & Title */}
            <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#1e3a5f]/15 to-[#c9a84c]/10 flex flex-shrink-0 items-center justify-center text-3xl shadow-inner">
                    📇
                </div>
                <div className="flex-1 min-w-0 pt-1">
                    <h3 className="text-xl font-bold text-[#1e3a5f] dark:text-[#e8e4db] truncate">{item.title}</h3>

                    {/* Badges / Pills */}
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#1e3a5f]/8 dark:bg-[#c9a84c]/15 text-[#1e3a5f] dark:text-[#c9a84c] border border-[#1e3a5f]/15 dark:border-[#c9a84c]/20 uppercase tracking-wide">
                            Flashcards
                        </span>
                        {isFlashcardSet && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30">
                                {flashcards.length} Cards
                            </span>
                        )}
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#1e3a5f]/5 dark:bg-white/5 text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50">
                            {new Date(item.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                        </span>
                    </div>
                </div>
            </div>

            {/* Description */}
            <p className="text-[#1e3a5f]/70 dark:text-[#c8c3b8] mb-6 line-clamp-2 min-h-[44px] leading-relaxed text-sm lg:text-base">
                {item.description || "A community-shared learning resource."}
            </p>

            {/* Expanded flashcard viewer */}
            <div className={`overflow-hidden transition-all duration-500 ease-in-out ${expanded ? 'max-h-[800px] opacity-100 mb-6' : 'max-h-0 opacity-0 mb-0'}`}>
                {expanded && isFlashcardSet && (
                    <div className="p-1 rounded-3xl bg-[#0f1a2b]/60 border border-[#1e3a5f]/20 shadow-inner">
                        <CommunityFlashcardViewer flashcards={flashcards} title={item.title} />
                    </div>
                )}
            </div>

            {/* Footer Actions */}
            <div className="flex items-center justify-between mt-auto pt-4 border-t border-[#1e3a5f]/10 dark:border-[#c9a84c]/10">
                <button
                    onClick={() => onUpvote(item.id)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-xl hover:bg-[#1e3a5f]/5 dark:hover:bg-[#c9a84c]/10 text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50 hover:text-[#c9a84c] dark:hover:text-[#c9a84c] transition-colors group/upvote"
                >
                    <svg className="w-5 h-5 group-hover/upvote:-translate-y-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 15l7-7 7 7" />
                    </svg>
                    <span className="font-semibold text-sm">{item.upvotes}</span>
                </button>

                {isFlashcardSet && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className={`px-5 py-2 text-sm font-bold rounded-xl shadow-lg transition-all active:scale-95 flex items-center gap-2
                            ${expanded
                                ? 'bg-[#1e3a5f]/60 hover:bg-[#1e3a5f]/70 text-white shadow-[#0f1a2b]/20'
                                : 'bg-[#1e3a5f] hover:bg-[#173050] text-white shadow-[#1e3a5f]/25'
                            }`}
                    >
                        {expanded ? (
                            <>
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                Close
                            </>
                        ) : (
                            <>
                                <span>📇</span> Study Now
                            </>
                        )}
                    </button>
                )}
            </div>
        </div>
    );
}

