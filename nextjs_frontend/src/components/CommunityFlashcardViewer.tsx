"use client";

import React, { useState } from "react";

interface FlashcardData {
    front: string;
    back: string;
    category?: string;
    difficulty?: string;
}

interface Props {
    flashcards: FlashcardData[];
    title: string;
}

export default function CommunityFlashcardViewer({ flashcards, title }: Props) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);

    if (!flashcards || flashcards.length === 0) return null;

    const card = flashcards[currentIndex];

    const goNext = () => {
        setIsFlipped(false);
        setTimeout(() => setCurrentIndex((prev) => (prev + 1) % flashcards.length), 150);
    };

    const goPrev = () => {
        setIsFlipped(false);
        setTimeout(() => setCurrentIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length), 150);
    };

    return (
        <div className="flex flex-col items-center gap-4 w-full">
            {/* Title bar */}
            <div className="flex items-center justify-between w-full">
                <h3 className="text-sm font-bold text-[#1e3a5f] dark:text-[#c8c3b8] truncate">
                    📇 {title}
                </h3>
                <span className="text-xs font-semibold text-[#c9a84c] bg-[#c9a84c]/10 px-2 py-0.5 rounded-full">
                    {currentIndex + 1} / {flashcards.length}
                </span>
            </div>

            {/* Flashcard with 3D flip */}
            <div
                className="relative w-full aspect-[3/2] cursor-pointer group"
                style={{ perspective: "1500px" }}
                onClick={() => setIsFlipped(!isFlipped)}
            >
                <div
                    className={`absolute inset-0 w-full h-full transition-all duration-[800ms] ease-[cubic-bezier(0.23,1,0.32,1)] shadow-xl rounded-2xl ${isFlipped ? "[transform:rotateY(180deg)]" : ""}`}
                    style={{ transformStyle: "preserve-3d" }}
                >
                    {/* Front Face */}
                    <div
                        className="absolute inset-0 w-full h-full rounded-2xl bg-gradient-to-br from-[#162236] to-[#0f1a2b] border border-[#1e3a5f]/30 flex flex-col p-5 shadow-[0_10px_40px_rgba(15,26,43,0.3)] hover:border-[#c9a84c]/30 transition-colors"
                        style={{ backfaceVisibility: "hidden" }}
                    >
                        <div className="flex justify-between items-center mb-3">
                            <span className="text-[9px] uppercase font-bold tracking-widest text-[#c9a84c] opacity-80 bg-[#c9a84c]/10 px-2 py-0.5 rounded-md">
                                Flashcard
                            </span>
                            <svg className="w-3.5 h-3.5 text-[#c9a84c]/40 opacity-50 group-hover:opacity-100 transition-opacity shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                            </svg>
                        </div>
                        <div className="flex-1 flex items-center justify-center text-center overflow-y-auto custom-scrollbar">
                            <div className="text-sm md:text-base lg:text-lg font-semibold text-white leading-relaxed tracking-wide drop-shadow-md">
                                {card.front}
                            </div>
                        </div>
                        <div className="mt-3 text-center">
                            <span className="text-[10px] uppercase tracking-wider text-[#c8c3b8]/40 group-hover:text-[#c9a84c]/70 transition-colors">Click to flip</span>
                        </div>
                    </div>

                    {/* Back Face */}
                    <div
                        className="absolute inset-0 w-full h-full rounded-2xl bg-gradient-to-br from-[#1e3a5f] to-[#0f2847] border border-[#c9a84c]/25 flex flex-col p-5 shadow-[0_0_50px_rgba(201,168,76,0.1)] [transform:rotateY(180deg)]"
                        style={{ backfaceVisibility: "hidden" }}
                    >
                        <div className="flex justify-between items-center mb-3">
                            <span className="text-[9px] uppercase font-bold tracking-widest text-[#c9a84c] opacity-80 bg-[#c9a84c]/10 px-2 py-0.5 rounded-md">
                                Answer
                            </span>
                        </div>
                        <div className="flex-1 flex items-center justify-center text-center overflow-y-auto custom-scrollbar">
                            <div className="text-xs md:text-sm lg:text-base font-medium text-[#f0ede6] leading-relaxed">
                                {card.back}
                            </div>
                        </div>
                        <div className="mt-3 text-center">
                            <div className="inline-flex items-center justify-center gap-1.5 text-[#c9a84c]/50">
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                                </svg>
                                <span className="text-[10px] uppercase tracking-wider">Flip back</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Category / Difficulty hint */}
            {(card.category || card.difficulty) && (
                <div className="w-full px-3 py-2 rounded-xl bg-[#c9a84c]/5 border border-[#c9a84c]/10 text-xs text-[#1e3a5f]/60 dark:text-[#c8c3b8]/50 backdrop-blur-md flex items-center gap-2">
                    <div className="p-1 rounded-full bg-[#c9a84c]/15 text-[#c9a84c]">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                    </div>
                    <span>
                        {card.category && `Category: ${card.category}`}
                        {card.category && card.difficulty && " | "}
                        {card.difficulty && `Difficulty: ${card.difficulty}`}
                    </span>
                </div>
            )}

            {/* Navigation buttons */}
            {flashcards.length > 1 && (
                <div className="flex items-center gap-3">
                    <button
                        onClick={(e) => { e.stopPropagation(); goPrev(); }}
                        className="w-8 h-8 flex items-center justify-center rounded-full bg-[#1e3a5f]/10 hover:bg-[#1e3a5f]/20 dark:bg-[#c9a84c]/10 dark:hover:bg-[#c9a84c]/20 border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 hover:text-[#1e3a5f] dark:hover:text-white transition-all"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                    </button>

                    {/* Dots */}
                    <div className="flex gap-1.5">
                        {flashcards.map((_, i) => (
                            <button
                                key={i}
                                onClick={(e) => { e.stopPropagation(); setIsFlipped(false); setCurrentIndex(i); }}
                                className={`w-2 h-2 rounded-full transition-all ${i === currentIndex ? "bg-[#c9a84c] scale-125" : "bg-[#1e3a5f]/20 dark:bg-[#c8c3b8]/20 hover:bg-[#c9a84c]/50"}`}
                            />
                        ))}
                    </div>

                    <button
                        onClick={(e) => { e.stopPropagation(); goNext(); }}
                        className="w-8 h-8 flex items-center justify-center rounded-full bg-[#1e3a5f]/10 hover:bg-[#1e3a5f]/20 dark:bg-[#c9a84c]/10 dark:hover:bg-[#c9a84c]/20 border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 hover:text-[#1e3a5f] dark:hover:text-white transition-all"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>
            )}
        </div>
    );
}
