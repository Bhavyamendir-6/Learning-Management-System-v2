"use client";

import React from "react";

/* ────────────────────────────────────────────────────────────────
   Human-readable labels for tool names and agent names.
   Makes the thinking indicator feel polished and user-friendly.
   ──────────────────────────────────────────────────────────────── */
const TOOL_LABELS: Record<string, string> = {
    generate_quiz: "Generating quiz questions",
    ask_question: "Searching document",
    generate_summary: "Creating summary",
    generate_flashcards: "Building flashcards",
    record_answer: "Recording answer",
    complete_quiz: "Completing quiz",
    retry_quiz: "Preparing retry quiz",
    start_tutoring_session: "Starting tutoring session",
    ask_followup: "Processing your response",
    check_understanding: "Checking understanding",
    save_learning_notes: "Saving notes",
    get_learning_notes: "Retrieving notes",
    upload_pdf: "Uploading document",
    batch_upload_pdf: "Uploading documents",
    list_files: "Listing files",
};

const AGENT_LABELS: Record<string, string> = {
    Quiz_Master: "Quiz Master",
    LearningContent_Agent: "Learning Content",
    AI_Tutor: "AI Tutor",
    PDF_Handler: "PDF Handler",
    Quiz_Historian: "Quiz Historian",
    LMS_Executive: "LMS Executive",
};

export interface ThinkingStep {
    id: string;
    type: "tool_call" | "agent_transfer";
    name: string;      // tool name or agent name
    agent: string;     // which agent triggered it
    status: "active" | "done";
    timestamp: number;
}

interface AgentThinkingIndicatorProps {
    steps: ThinkingStep[];
    isVisible: boolean;
}

function getStepLabel(step: ThinkingStep): string {
    if (step.type === "agent_transfer") {
        const label = AGENT_LABELS[step.name] || step.name;
        return `Routing to ${label}`;
    }
    return TOOL_LABELS[step.name] || step.name.replace(/_/g, " ");
}

function getStepIcon(step: ThinkingStep): React.ReactNode {
    if (step.status === "done") {
        return (
            <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
        );
    }

    // Active pulsing dot
    return (
        <span className="relative flex h-3 w-3">
            <span className="thinking-ping absolute inline-flex h-full w-full rounded-full bg-[#c9a84c] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-[#1e3a5f] dark:bg-[#c9a84c]"></span>
        </span>
    );
}

export default function AgentThinkingIndicator({ steps, isVisible }: AgentThinkingIndicatorProps) {
    if (!isVisible || steps.length === 0) return null;

    return (
        <div className={`thinking-indicator ${isVisible ? 'thinking-visible' : 'thinking-hidden'}`}>
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
                <div className="thinking-header-orb">
                    <svg className="w-3.5 h-3.5 text-[#c9a84c]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        />
                    </svg>
                </div>
                <span className="thinking-header-text">Thinking</span>
                <span className="thinking-header-dots">
                    <span className="thinking-dot" style={{ animationDelay: "0ms" }}>.</span>
                    <span className="thinking-dot" style={{ animationDelay: "200ms" }}>.</span>
                    <span className="thinking-dot" style={{ animationDelay: "400ms" }}>.</span>
                </span>
            </div>

            {/* Steps */}
            <div className="thinking-steps">
                {steps.map((step, idx) => (
                    <div
                        key={step.id}
                        className={`thinking-step ${step.status === "done" ? "thinking-step-done" : "thinking-step-active"}`}
                        style={{ animationDelay: `${idx * 80}ms` }}
                    >
                        <div className="thinking-step-icon">
                            {getStepIcon(step)}
                        </div>
                        <span className="thinking-step-label">
                            {getStepLabel(step)}
                        </span>
                        {step.agent && step.type === "tool_call" && (
                            <span className="thinking-step-agent">
                                {AGENT_LABELS[step.agent] || step.agent}
                            </span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
