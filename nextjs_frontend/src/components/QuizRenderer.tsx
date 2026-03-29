"use client";

import React, { useState } from "react";
import { fetchAPI } from "../lib/api";

interface Question {
    question_number: number;
    question_text: string;
    options: string[];
    correct_answer: string;
    hint?: string;
    explanation?: string;
}

// Raw question shape from the backend (options as object)
interface RawQuestion {
    question_number: number;
    question?: string;
    question_text?: string;
    options: Record<string, string> | string[];
    correct_answer: string;
    hint?: string;
    explanation?: string;
}

interface QuizData {
    quiz_session_id?: string;
    document_name?: string;
    document?: string;
    status?: string;
    questions: RawQuestion[];
}

interface QuizRendererProps {
    data: QuizData;
    onComplete?: () => void;
    onPublish?: () => void;
}

/**
 * Normalize a raw question from the backend into the format the renderer expects.
 * Handles both object options ({"A": "text"}) and array options (["A) text"]).
 */
function normalizeQuestion(raw: RawQuestion): Question {
    let options: string[];
    if (Array.isArray(raw.options)) {
        options = raw.options;
    } else {
        // Convert {"A": "text", "B": "text"} → ["A) text", "B) text"]
        options = Object.entries(raw.options).map(([letter, text]) => `${letter}) ${text}`);
    }
    return {
        question_number: raw.question_number,
        question_text: raw.question_text || raw.question || "",
        options,
        correct_answer: raw.correct_answer,
        hint: raw.hint,
        explanation: raw.explanation,
    };
}

export default function QuizRenderer({ data, onComplete, onPublish }: QuizRendererProps) {
    // Normalize all questions on mount
    const questions: Question[] = data.questions.map(normalizeQuestion);
    const documentName = data.document_name || data.document;
    const [answers, setAnswers] = useState<Record<number, string>>({});
    const [submitted, setSubmitted] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // If there's no session ID, we can't submit it to the backend realistically.
    // But we can at least show the quiz.
    const sessionId = data.quiz_session_id || "demo-session";

    const handleSelect = (qNum: number, opt: string) => {
        if (submitted) return;
        setAnswers((prev) => ({ ...prev, [qNum]: opt }));
    };

    const handleSubmit = async () => {
        setSubmitting(true);
        const answersPayload = questions.map((q) => {
            const userAnsStr = answers[q.question_number] || "";
            // The backend expects "A", "B", "C", "D"
            // The options are often "A) text"
            const userChoice = userAnsStr.charAt(0).toUpperCase();
            const isCorrect = userChoice === q.correct_answer;

            return {
                question_number: q.question_number,
                question_text: q.question_text,
                user_answer: userChoice || "NONE",
                correct_answer: q.correct_answer,
                is_correct: isCorrect,
            };
        });

        try {
            if (sessionId !== "demo-session") {
                await fetchAPI("/quiz/record-answers", {
                    method: "POST",
                    body: JSON.stringify({
                        quiz_session_id: sessionId,
                        answers: answersPayload,
                    }),
                });
            }
            setSubmitted(true);
            if (onComplete) onComplete();
        } catch (err) {
            console.error("Failed to submit quiz", err);
        } finally {
            setSubmitting(false);
        }
    };

    const allAnswered = Object.keys(answers).length === questions.length;

    return (
        <div className="bg-white dark:bg-[#162236] rounded-xl border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 shadow-sm overflow-hidden mt-4 mb-2 animate-fade-in">
            <div className="bg-[#1e3a5f]/5 dark:bg-[#1e3a5f]/30 p-4 border-b border-[#1e3a5f]/10 dark:border-[#c9a84c]/10">
                <h3 className="font-bold text-[#1e3a5f] dark:text-[#c9a84c] flex items-center gap-2" style={{ fontFamily: 'var(--font-serif)' }}>
                    <svg className="w-5 h-5 text-[#1e3a5f] dark:text-[#c9a84c]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    Interactive Quiz {documentName && `- ${documentName}`}
                </h3>
            </div>

            <div className="p-5 space-y-6">
                {questions.map((q, idx) => {
                    const userAnsStr = answers[q.question_number] || "";
                    const userChoice = userAnsStr.charAt(0).toUpperCase();
                    const isCorrect = submitted && userChoice === q.correct_answer;
                    const isWrong = submitted && userChoice !== q.correct_answer && userChoice !== "";

                    return (
                        <div key={idx} className="space-y-3">
                            <p className="font-semibold text-[#1e3a5f] dark:text-[#e8e4db]">
                                {q.question_number}. {q.question_text}
                            </p>
                            <div className="space-y-2 pl-4">
                                {q.options.map((opt, oIdx) => {
                                    const optLetter = opt.charAt(0).toUpperCase();
                                    let btnClass = "border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 hover:bg-[#1e3a5f]/3 dark:hover:bg-[#c9a84c]/5";
                                    let dotClass = "border-[#1e3a5f]/20 dark:border-[#c9a84c]/20";

                                    if (answers[q.question_number] === opt) {
                                        btnClass = "border-[#1e3a5f] bg-[#1e3a5f]/8 dark:border-[#c9a84c] dark:bg-[#c9a84c]/10";
                                        dotClass = "border-[#1e3a5f] bg-[#1e3a5f] dark:border-[#c9a84c] dark:bg-[#c9a84c]";
                                    }

                                    if (submitted) {
                                        if (optLetter === q.correct_answer) {
                                            btnClass = "border-green-500 bg-green-50 dark:bg-green-900/20";
                                            dotClass = "border-green-500 bg-green-500";
                                        } else if (answers[q.question_number] === opt && optLetter !== q.correct_answer) {
                                            btnClass = "border-red-500 bg-red-50 dark:bg-red-900/20";
                                            dotClass = "border-red-500 bg-red-500";
                                        } else {
                                            btnClass = "border-[#1e3a5f]/10 dark:border-[#c9a84c]/5 opacity-50";
                                            dotClass = "border-[#1e3a5f]/15 dark:border-[#c9a84c]/10";
                                        }
                                    }

                                    return (
                                        <button
                                            key={oIdx}
                                            onClick={() => handleSelect(q.question_number, opt)}
                                            disabled={submitted}
                                            className={`w-full text-left px-4 py-3 border rounded-lg transition-colors flex items-center gap-3 ${btnClass}`}
                                        >
                                            <div className={`w-4 h-4 rounded-full border flex-shrink-0 ${dotClass}`}></div>
                                            <span className="text-sm text-[#1e3a5f] dark:text-[#e8e4db]">{opt}</span>
                                        </button>
                                    );
                                })}
                            </div>

                            {submitted && (
                                <div className={`mt-2 p-3 rounded-md text-sm ${isCorrect ? "bg-green-100/50 text-green-800 dark:text-green-200" : "bg-red-100/50 text-red-800 dark:text-red-200"}`}>
                                    <span className="font-bold">{isCorrect ? "Correct!" : "Incorrect."}</span> The correct answer is {q.correct_answer}.
                                    {q.explanation && <div className="mt-1 text-[#1e3a5f]/80 dark:text-[#c8c3b8]/80">{q.explanation}</div>}
                                    {!q.explanation && q.hint && <div className="mt-1 text-[#1e3a5f]/60 dark:text-[#c8c3b8]/60 italic">Hint: {q.hint}</div>}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="bg-[#1e3a5f]/3 dark:bg-[#0a1220]/50 p-4 border-t border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 flex justify-end">
                {!submitted ? (
                    <button
                        onClick={handleSubmit}
                        disabled={!allAnswered || submitting}
                        className="px-6 py-2 bg-[#1e3a5f] hover:bg-[#173050] text-white font-medium rounded-lg disabled:opacity-50 transition-colors shadow-sm"
                    >
                        {submitting ? "Submitting..." : "Submit Answers"}
                    </button>
                ) : (
                    <div className="flex items-center gap-4">
                        {onPublish && (
                            <button
                                onClick={onPublish}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1e3a5f]/10 hover:bg-[#1e3a5f]/20 dark:bg-[#c9a84c]/10 dark:hover:bg-[#c9a84c]/20 border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 text-[#1e3a5f] dark:text-[#c9a84c] text-sm font-bold transition-all shadow-sm"
                            >
                                <span>🌍</span> Publish to Community
                            </button>
                        )}
                        <div className="text-green-600 dark:text-green-400 font-bold flex items-center gap-2">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Quiz Completed
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
