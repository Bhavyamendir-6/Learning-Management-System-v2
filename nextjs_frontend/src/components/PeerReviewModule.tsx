import React, { useEffect, useState } from 'react';
import { getPendingPeerReviews, submitPeerGrade } from '@/lib/api';

export interface PendingReview {
    id: string;
    item_id: string;
    original_question: string;
    student_answer: string;
    created_at: string;
}

export default function PeerReviewModule() {
    const [reviews, setReviews] = useState<PendingReview[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeReview, setActiveReview] = useState<PendingReview | null>(null);
    const [score, setScore] = useState<number | ''>('');
    const [feedback, setFeedback] = useState('');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        loadReviews();
    }, []);

    const loadReviews = async () => {
        setLoading(true);
        try {
            const res = await getPendingPeerReviews();
            setReviews(res.pending_reviews || []);
            if (res.pending_reviews && res.pending_reviews.length > 0) {
                setActiveReview(res.pending_reviews[0]);
            } else {
                setActiveReview(null);
            }
        } catch (err) {
            console.error("Failed to load peer reviews", err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!activeReview || score === '' || feedback.trim() === '') return;

        setSubmitting(true);
        try {
            await submitPeerGrade(activeReview.id, Number(score), feedback);
            setScore('');
            setFeedback('');
            // Optimistically remove from list
            const newReviews = reviews.filter(r => r.id !== activeReview.id);
            setReviews(newReviews);
            setActiveReview(newReviews.length > 0 ? newReviews[0] : null);
        } catch (err) {
            console.error("Failed to submit grade", err);
            alert("Failed to submit grade.");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#c9a84c]"></div>
            </div>
        );
    }

    if (reviews.length === 0) {
        return (
            <div className="py-20 text-center flex flex-col items-center justify-center bg-white/40 dark:bg-[#0f1a2b]/40 rounded-3xl border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 border-dashed">
                <span className="text-6xl mb-4 opacity-50">🎉</span>
                <h3 className="text-xl font-bold text-[#1e3a5f] dark:text-[#e8e4db] mb-2">You're all caught up!</h3>
                <p className="text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50 max-w-sm">There are no peer reviews assigned to you right now. Check back later.</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col lg:flex-row gap-8 bg-white/30 dark:bg-[#0f1a2b]/40 backdrop-blur-xl border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 rounded-3xl overflow-hidden shadow-2xl">
            {/* Left Sidebar: List of pending reviews */}
            <div className="lg:w-1/3 border-b lg:border-b-0 lg:border-r border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 p-6 flex flex-col max-h-[600px] overflow-y-auto custom-scrollbar bg-[#1e3a5f]/3 dark:bg-[#0a1220]/30">
                <h3 className="text-lg font-extrabold text-[#1e3a5f] dark:text-[#e8e4db] mb-4 px-2 tracking-tight" style={{ fontFamily: 'var(--font-serif)' }}>Pending Tasks <span className="text-[#c9a84c] bg-[#c9a84c]/10 px-2.5 py-0.5 rounded-full text-sm ml-2">{reviews.length}</span></h3>
                <div className="space-y-3">
                    {reviews.map(review => (
                        <button
                            key={review.id}
                            onClick={() => setActiveReview(review)}
                            className={`w-full text-left p-4 rounded-2xl transition-all border ${activeReview?.id === review.id
                                ? 'bg-white dark:bg-[#1e3a5f]/30 border-[#1e3a5f] dark:border-[#c9a84c] shadow-md'
                                : 'bg-white/50 dark:bg-[#0f1a2b]/50 border-transparent hover:border-[#1e3a5f]/15 dark:hover:border-[#c9a84c]/15 hover:bg-white dark:hover:bg-[#c9a84c]/5'
                                }`}
                        >
                            <div className="text-xs font-bold text-[#c9a84c] mb-1 flex items-center gap-1.5 uppercase tracking-wider">
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                {new Date(review.created_at).toLocaleDateString()}
                            </div>
                            <h4 className="font-semibold text-[#1e3a5f] dark:text-[#e8e4db] line-clamp-2">{review.original_question}</h4>
                        </button>
                    ))}
                </div>
            </div>

            {/* Right Area: Grading Interface */}
            <div className="lg:w-2/3 p-8 flex flex-col relative z-0">
                {activeReview ? (
                    <div className="flex-1 overflow-y-auto animate-fade-in custom-scrollbar pr-4">
                        <div className="mb-8">
                            <span className="text-xs font-bold uppercase tracking-widest text-[#1e3a5f]/40 dark:text-[#c8c3b8]/40 mb-2 block">Question</span>
                            <div className="text-xl font-bold text-[#1e3a5f] dark:text-white leading-relaxed" style={{ fontFamily: 'var(--font-serif)' }}>
                                {activeReview.original_question}
                            </div>
                        </div>

                        <div className="mb-8 bg-[#1e3a5f]/3 dark:bg-[#1e3a5f]/15 border border-[#1e3a5f]/10 dark:border-[#c9a84c]/15 rounded-2xl p-6 relative">
                            <div className="absolute top-0 right-8 -translate-y-1/2 bg-[#1e3a5f]/8 dark:bg-[#1e3a5f]/50 border border-[#1e3a5f]/15 dark:border-[#c9a84c]/20 text-[#1e3a5f] dark:text-[#c9a84c] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide flex items-center gap-1.5">
                                <span>👤</span> Student's Answer
                            </div>
                            <p className="text-[#1e3a5f]/80 dark:text-[#c8c3b8] leading-relaxed font-medium mt-2 whitespace-pre-wrap">
                                {activeReview.student_answer}
                            </p>
                        </div>

                        <hr className="border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 mb-8" />

                        <form onSubmit={handleSubmit} className="mb-4">
                            <h4 className="text-lg font-extrabold text-[#1e3a5f] dark:text-[#e8e4db] mb-6 flex items-center gap-2" style={{ fontFamily: 'var(--font-serif)' }}>
                                <span>⚖️</span> Provide Your Assessment
                            </h4>

                            <div className="mb-6">
                                <label className="block text-sm font-bold text-[#1e3a5f] dark:text-[#c8c3b8] mb-2 text-[13px] uppercase tracking-wider">
                                    Grade Score (0-100)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="100"
                                    required
                                    value={score}
                                    onChange={(e) => setScore(e.target.value === '' ? '' : Number(e.target.value))}
                                    className="w-32 bg-white dark:bg-[#0a1220]/70 border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 rounded-xl px-4 py-3 text-lg font-bold text-[#1e3a5f] dark:text-white outline-none focus:ring-2 focus:ring-[#c9a84c]/40 transition-all text-center"
                                    placeholder="85"
                                />
                            </div>

                            <div className="mb-8">
                                <label className="block text-sm font-bold text-[#1e3a5f] dark:text-[#c8c3b8] mb-2 text-[13px] uppercase tracking-wider">
                                    Constructive Feedback
                                </label>
                                <textarea
                                    required
                                    rows={4}
                                    value={feedback}
                                    onChange={(e) => setFeedback(e.target.value)}
                                    placeholder="Explain what they did well and where they can improve..."
                                    className="w-full bg-white dark:bg-[#0a1220]/70 border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 rounded-xl px-5 py-4 text-[#1e3a5f] dark:text-white outline-none focus:ring-2 focus:ring-[#c9a84c]/40 transition-all resize-none shadow-sm"
                                ></textarea>
                            </div>

                            <div className="flex justify-end">
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="px-8 py-3 bg-gradient-to-r from-[#1e3a5f] to-[#2c5282] text-white font-bold rounded-xl shadow-lg hover:shadow-[#1e3a5f]/25 transition-all active:scale-95 disabled:opacity-50 disabled:scale-100 flex items-center gap-2"
                                >
                                    {submitting ? (
                                        <>
                                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                            Submitting...
                                        </>
                                    ) : (
                                        <>
                                            Submit Grade <span>🎯</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
