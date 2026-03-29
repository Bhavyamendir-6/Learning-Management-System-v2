"use client";

import React, { useMemo, useState, useCallback, useEffect, useRef } from "react";
import QuizRenderer from "./QuizRenderer";
import BufferingAnimation from "./BufferingAnimation";
import AgentThinkingIndicator from "./AgentThinkingIndicator";
import type { ThinkingStep } from "./AgentThinkingIndicator";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import type { Components } from "react-markdown";
import Flashcard from "./Flashcard";

interface ChatBubbleProps {
    role: "user" | "agent";
    text: string;
    ts?: string;
    isStreaming?: boolean;
    animateTyping?: boolean;
    thinkingSteps?: ThinkingStep[];
}

/* ─── Copy-to-clipboard button for code blocks ─── */
function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);
    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }, [text]);

    return (
        <button
            onClick={handleCopy}
            className="absolute top-3 right-3 px-2.5 py-1 rounded-md bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-all duration-200 backdrop-blur-sm flex items-center gap-1.5"
            title="Copy code"
        >
            {copied ? (
                <>
                    <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                </>
            ) : (
                <>
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy
                </>
            )}
        </button>
    );
}

/* ─── Custom Markdown renderers for stunning formatting ─── */
const baseComponents: Components = {

    /* ── Headings ── */
    h1: ({ children, ...props }) => (
        <h1 className="agent-heading agent-h1" {...props}>
            <span className="heading-accent" />
            {children}
        </h1>
    ),
    h2: ({ children, ...props }) => (
        <h2 className="agent-heading agent-h2" {...props}>
            <span className="heading-accent" />
            {children}
        </h2>
    ),
    h3: ({ children, ...props }) => (
        <h3 className="agent-heading agent-h3" {...props}>
            {children}
        </h3>
    ),
    h4: ({ children, ...props }) => (
        <h4 className="agent-heading agent-h4" {...props}>
            {children}
        </h4>
    ),

    /* ── Paragraphs ── */
    p: ({ children, ...props }) => (
        <p className="agent-paragraph" {...props}>
            {children}
        </p>
    ),

    /* ── Bold / Strong ── */
    strong: ({ children, ...props }) => (
        <strong className="agent-strong" {...props}>
            {children}
        </strong>
    ),

    /* ── Emphasis / Italic ── */
    em: ({ children, ...props }) => (
        <em className="agent-em" {...props}>
            {children}
        </em>
    ),

    /* ── Links ── */
    a: ({ children, href, ...props }) => (
        <a
            href={href}
            className="agent-link"
            target="_blank"
            rel="noopener noreferrer"
            {...props}
        >
            {children}
            <svg className="inline-block w-3 h-3 ml-1 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
        </a>
    ),

    /* ── Unordered Lists ── */
    ul: ({ children, ...props }) => (
        <ul className="agent-ul" {...props}>
            {children}
        </ul>
    ),

    /* ── Ordered Lists ── */
    ol: ({ children, ...props }) => (
        <ol className="agent-ol" {...props}>
            {children}
        </ol>
    ),

    /* ── List Items ── */
    li: ({ children, className, ...props }) => {
        // If there's an onClick handler passed down, inject it directly
        // We handle the click logic inside ChatBubble where we have access to the handler
        return (
            <li className={`agent-li ${className || ""}`} {...props} >
                <span className="li-marker" />
                <span className="li-content">{children}</span>
            </li>
        );
    },

    /* ── Blockquotes ── */
    blockquote: ({ children, ...props }) => (
        <blockquote className="agent-blockquote" {...props}>
            <div className="bq-icon">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10H14.017zm-14.017 0v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10H0z" />
                </svg>
            </div>
            <div className="bq-content">{children}</div>
        </blockquote>
    ),

    /* ── Horizontal Rules ── */
    hr: ({ ...props }) => (
        <div className="agent-hr-wrapper" {...props}>
            <div className="agent-hr">
                <div className="hr-diamond" />
            </div>
        </div>
    ),

    /* ── Code Blocks ── */
    pre: ({ children, ...props }) => {
        // Extract the raw text from code children for the copy button
        let codeText = "";
        let language = "";
        React.Children.forEach(children, (child) => {
            if (React.isValidElement(child) && child.props) {
                const childProps = child.props as { children?: React.ReactNode; className?: string };
                if (childProps.className) {
                    const match = childProps.className.match(/language-(\w+)/);
                    if (match) language = match[1];
                }
                if (typeof childProps.children === "string") {
                    codeText = childProps.children;
                }
            }
        });

        return (
            <div className="agent-code-block">
                <div className="code-header">
                    <div className="code-dots">
                        <span className="dot dot-red" />
                        <span className="dot dot-yellow" />
                        <span className="dot dot-green" />
                    </div>
                    {language && (
                        <span className="code-lang">{language}</span>
                    )}
                    <CopyButton text={codeText} />
                </div>
                <pre className="code-pre" {...props}>{children}</pre>
            </div>
        );
    },

    /* ── Inline Code ── */
    code: ({ children, className, ...props }) => {
        // If it has a language class, it's inside a <pre> — render normally
        if (className) {
            return <code className={className} {...props}>{children}</code>;
        }
        // Inline code
        return (
            <code className="agent-inline-code" {...props}>
                {children}
            </code>
        );
    },

    /* ── Tables ── */
    table: ({ children, ...props }) => (
        <div className="agent-table-wrapper">
            <table className="agent-table" {...props}>
                {children}
            </table>
        </div>
    ),
    thead: ({ children, ...props }) => (
        <thead className="agent-thead" {...props}>{children}</thead>
    ),
    tbody: ({ children, ...props }) => (
        <tbody className="agent-tbody" {...props}>{children}</tbody>
    ),
    tr: ({ children, ...props }) => (
        <tr className="agent-tr" {...props}>{children}</tr>
    ),
    th: ({ children, ...props }) => (
        <th className="agent-th" {...props}>{children}</th>
    ),
    td: ({ children, ...props }) => (
        <td className="agent-td" {...props}>{children}</td>
    ),
};

const getMarkdownComponents = (onOptionClick?: (option: string) => void, onPublish?: () => void): any => ({
    ...baseComponents,
    li: ({ children, className, ...props }: any) => {
        // Find if this list item is an option (A), B), etc.)
        const handleClick = () => {
            if (!onOptionClick) return;

            // Extract text from children to see if it starts with A), B), C), D)
            let textContent = "";
            React.Children.forEach(children, (child) => {
                if (typeof child === "string") textContent += child;
                // If the child is an element (like a bold tag `**A)**`), we extract its inner string
                if (React.isValidElement(child) && child.props && "children" in (child.props as any)) {
                    const childProps = child.props as any;
                    if (typeof childProps.children === "string") {
                        textContent += childProps.children;
                    } else if (Array.isArray(childProps.children)) {
                        textContent += childProps.children.join("");
                    }
                }
            });

            const match = textContent.trim().match(/^([A-Da-d])\)/);
            if (match) {
                onOptionClick(match[1].toUpperCase());
            }
        };

        return (
            <li
                className={`agent-li ${className || ""} ${onOptionClick ? 'cursor-pointer' : ''}`}
                onClick={handleClick}
                {...props}
            >
                <span className="li-marker" />
                <span className="li-content">{children}</span>
            </li>
        );
    },
    /* ── Flashcard ── */
    flashcard: ({ children, ...props }: any) => (
        <Flashcard onPublish={onPublish} {...props}>{children}</Flashcard>
    ),
});

export default function ChatBubble({ role, text, ts, isStreaming, animateTyping, thinkingSteps, onOptionClick, onPublish }: ChatBubbleProps & { onOptionClick?: (opt: string) => void, onPublish?: () => void }) {
    const isUser = role === "user";

    const { parsedText, quizData } = useMemo(() => {
        let parsedText = text;
        let quizData = null;

        if (!isUser && !isStreaming) {
            /**
             * Helper: try to parse a JSON string, with fallbacks for common LLM quirks
             * (single quotes, Python True/False/None, trailing commas).
             */
            const tryParseJSON = (raw: string): any | null => {
                const str = raw.trim();
                if (!str.startsWith("{") && !str.startsWith("[")) return null;
                try {
                    return JSON.parse(str);
                } catch {
                    try {
                        const clean = str
                            .replace(/'/g, '"')
                            .replace(/\bTrue\b/g, 'true')
                            .replace(/\bFalse\b/g, 'false')
                            .replace(/\bNone\b/g, 'null')
                            .replace(/,\s*([}\]])/g, '$1'); // trailing commas
                        return JSON.parse(clean);
                    } catch {
                        return null;
                    }
                }
            };

            /** Helper: unwrap LLM wrapper keys like "generate_quiz_response" */
            const unwrapQuizObj = (obj: any): any => {
                if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return obj;
                // If it already has questions, return as-is
                if (obj.questions && Array.isArray(obj.questions)) return obj;
                // Check one level deep — the LLM may wrap in "generate_quiz_response", etc.
                const keys = Object.keys(obj);
                for (const key of keys) {
                    const val = obj[key];
                    if (val && typeof val === 'object' && !Array.isArray(val)) {
                        if (val.questions && Array.isArray(val.questions)) return val;
                    }
                }
                return obj;
            };

            /** Helper: check if a parsed object looks like quiz data */
            const isQuizData = (obj: any): boolean => {
                if (!obj) return false;
                const unwrapped = unwrapQuizObj(obj);
                // Direct {questions: [...]} shape
                if (unwrapped.questions && Array.isArray(unwrapped.questions) && unwrapped.questions.length > 0) return true;
                // Bare array of question objects
                if (Array.isArray(obj) && obj.length > 0 && (obj[0].question_number !== undefined || obj[0].question_text !== undefined || obj[0].question !== undefined)) return true;
                return false;
            };

            /** Helper: normalize parsed data into {questions: [...]} shape */
            const normalizeQuizObj = (parsed: any): any => {
                if (Array.isArray(parsed)) return { questions: parsed };
                return unwrapQuizObj(parsed);
            };

            // ── Pattern 1: ```json ... ``` fenced code block ──
            // Case-insensitive, handles any whitespace/CRLF variant
            const codeBlockRegex = /```json\s*([\s\S]*?)```/gi;
            let match = codeBlockRegex.exec(text);
            while (match && match[1]) {
                const parsed = tryParseJSON(match[1]);
                if (isQuizData(parsed)) {
                    quizData = normalizeQuizObj(parsed);
                    parsedText = text.replace(match[0], "").trim();
                    break;
                }
                match = codeBlockRegex.exec(text);
            }

            // ── Pattern 2: Any ``` ... ``` code block (LLM may omit "json" language tag) ──
            if (!quizData) {
                const anyCodeBlock = /```\s*\n([\s\S]*?)```/g;
                let m2 = anyCodeBlock.exec(text);
                while (m2 && m2[1]) {
                    const parsed = tryParseJSON(m2[1]);
                    if (isQuizData(parsed)) {
                        quizData = normalizeQuizObj(parsed);
                        parsedText = text.replace(m2[0], "").trim();
                        break;
                    }
                    m2 = anyCodeBlock.exec(text);
                }
            }

            // ── Pattern 3: Bare JSON object with "questions" key (no code block) ──
            // Uses brace-matching to find the true end of the JSON object.
            if (!quizData) {
                const questionsIdx = text.indexOf('"questions"');
                if (questionsIdx !== -1) {
                    const start = text.lastIndexOf("{", questionsIdx);
                    if (start !== -1) {
                        try {
                            let depth = 0;
                            let end = start;
                            let inString = false;
                            while (end < text.length) {
                                const ch = text[end];
                                if (inString) {
                                    if (ch === "\\") { end++; } // skip escaped char
                                    else if (ch === '"') { inString = false; }
                                } else {
                                    if (ch === '"') { inString = true; }
                                    else if (ch === "{" || ch === "[") { depth++; }
                                    else if (ch === "}" || ch === "]") {
                                        depth--;
                                        if (depth === 0) { end++; break; }
                                    }
                                }
                                end++;
                            }
                            const jsonStr = text.slice(start, end);
                            const parsed = tryParseJSON(jsonStr);
                            if (isQuizData(parsed)) {
                                quizData = normalizeQuizObj(parsed);
                                parsedText = text.slice(0, start).trim();
                            }
                        } catch (e) {
                            console.warn("[ChatBubble] Pattern 3 JSON parse failed:", e);
                        }
                    }
                }
            }

            // ── Pattern 4: Look for "question_number" anywhere — LLM may have dumped
            //    the questions array without a wrapper object ──
            if (!quizData) {
                const arrIdx = text.indexOf('"question_number"');
                if (arrIdx !== -1) {
                    const arrStart = text.lastIndexOf("[", arrIdx);
                    if (arrStart !== -1) {
                        try {
                            let depth = 0;
                            let end = arrStart;
                            let inString = false;
                            while (end < text.length) {
                                const ch = text[end];
                                if (inString) {
                                    if (ch === "\\") { end++; }
                                    else if (ch === '"') { inString = false; }
                                } else {
                                    if (ch === '"') { inString = true; }
                                    else if (ch === "[" || ch === "{") { depth++; }
                                    else if (ch === "]" || ch === "}") {
                                        depth--;
                                        if (depth === 0) { end++; break; }
                                    }
                                }
                                end++;
                            }
                            const jsonStr = text.slice(arrStart, end);
                            const parsed = tryParseJSON(jsonStr);
                            if (isQuizData(parsed)) {
                                quizData = normalizeQuizObj(parsed);
                                parsedText = text.slice(0, arrStart).trim();
                            }
                        } catch (e) {
                            console.warn("[ChatBubble] Pattern 4 JSON parse failed:", e);
                        }
                    }
                }
            }
        }

        return { parsedText, quizData };
    }, [text, isUser, isStreaming]);

    /* ─── Typewriter Effect ─── */
    const isStructuredOutput = useMemo(() => {
        return parsedText.includes("```json") ||
            parsedText.includes("<flashcard>") ||
            quizData !== null;
    }, [parsedText, quizData]);

    const [typedText, setTypedText] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const typingIndexRef = useRef(0);
    const wordsRef = useRef<string[]>([]);

    useEffect(() => {
        if (!isUser && animateTyping && !isStructuredOutput) {
            // Split the parsedText into words (keeping spaces attached or as separate tokens)
            // The regex (\S+|\s+) splits into words and spaces.
            wordsRef.current = parsedText.match(/(\S+|\s+)/g) || [];

            // If words have been added, and we aren't currently typing things out, start typing
            if (wordsRef.current.length > typingIndexRef.current && !isTyping) {
                setIsTyping(true);
            }
        } else {
            // Either it's a user message, not animating, or a structured output.
            // Just show the whole text immediately.
            setTypedText(parsedText);
            setIsTyping(false);
        }
    }, [parsedText, isUser, animateTyping, isStructuredOutput]);

    useEffect(() => {
        if (!isTyping) return;

        const interval = setInterval(() => {
            if (typingIndexRef.current >= wordsRef.current.length) {
                // Done typing for now
                if (!isStreaming) {
                    setIsTyping(false); // Only completely stop typing if the backend stream is also done
                }
                clearInterval(interval);
                return;
            }

            const nextWord = wordsRef.current[typingIndexRef.current];
            setTypedText(prev => prev + nextWord);
            typingIndexRef.current += 1;
        }, 30); // 30ms per word roughly mimics fast human reading/typing speed

        return () => clearInterval(interval);
    }, [isTyping, parsedText, isStreaming]);

    // If an agent is streaming and there is NO text yet, just show the Ring of Power loader!
    const showBuffering = !isUser && isStreaming && parsedText.trim() === "";

    return (
        <div
            className={`flex w-full ${isUser ? "justify-end" : "justify-start"} mb-8 animate-slide-up group`}
        >
            {showBuffering ? (
                // Thinking indicator + majestic loader
                <div className="flex flex-col items-start gap-3 p-4">
                    {thinkingSteps && thinkingSteps.length > 0 && (
                        <AgentThinkingIndicator
                            steps={thinkingSteps}
                            isVisible={true}
                        />
                    )}
                    {(!thinkingSteps || thinkingSteps.length === 0) && (
                        <BufferingAnimation size="md" />
                    )}
                </div>
            ) : (
                <div
                    className={`relative max-w-[85%] sm:max-w-[75%] px-6 py-5 rounded-3xl text-[15px] leading-relaxed transition-all duration-300 ${isUser
                        ? "message-user text-white"
                        : "message-agent glass-ultra"
                        }`}
                >
                    {!isUser && (
                        <div className="absolute -left-12 top-0 w-9 h-9 rounded-full bg-gradient-to-br from-[#1e3a5f] to-[#2c5282] flex items-center justify-center text-white shadow-[0_0_15px_rgba(30,58,95,0.3)] ring-2 ring-[#0f1a2b]">
                            {/* Futuristic AI Icon */}
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                        </div>
                    )}

                    <div className="whitespace-pre-wrap font-sans space-y-4">
                        {isUser ? (
                            <span className="text-white">{parsedText}</span>
                        ) : (
                            <div className="agent-response-body">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    rehypePlugins={[rehypeHighlight, rehypeRaw]}
                                    components={getMarkdownComponents(onOptionClick, onPublish)}
                                >
                                    {typedText}
                                </ReactMarkdown>
                            </div>
                        )}
                        {quizData && <QuizRenderer data={quizData} onPublish={onPublish} />}
                        {(isStreaming || isTyping) && parsedText.trim() !== "" && (
                            <span className="inline-block w-2 h-5 ml-1 bg-gradient-to-b from-[#c9a84c] to-[#d4af37] animate-pulse align-middle rounded-full shadow-[0_0_8px_rgba(201,168,76,0.6)]"></span>
                        )}
                    </div>

                    {ts && (
                        <div
                            className={`text-[11px] mt-3 font-semibold tracking-wider opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${isUser
                                ? "text-white/60 text-right"
                                : "text-[var(--text-color)] opacity-50 text-left"
                                }`}
                        >
                            {ts}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
