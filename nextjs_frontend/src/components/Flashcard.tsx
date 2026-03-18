import React, { useState, ReactNode, isValidElement } from "react";

export default function Flashcard({ children, onPublish }: { children: ReactNode, onPublish?: () => void }) {
    const [isFlipped, setIsFlipped] = useState(false);

    let frontContent: ReactNode[] = [];
    let backContent: ReactNode[] = [];
    let hindsContent: ReactNode[] = [];

    // Helper to recursively find our custom tags.
    // rehype-raw translates <front> tags into React elements with type === "front".
    const extractSlots = (nodes: ReactNode) => {
        const childrenArray = React.Children.toArray(nodes);
        for (const child of childrenArray) {
            if (isValidElement(child)) {
                const props = child.props as any;
                if (child.type === "front") {
                    frontContent.push(props.children);
                } else if (child.type === "back") {
                    backContent.push(props.children);
                } else if (child.type === "hinds") {
                    hindsContent.push(props.children);
                } else {
                    // Try to search deeper in case remark wrapped them in paragraphs
                    if (props && props.children) {
                        extractSlots(props.children);
                    }
                }
            }
        }
    };

    extractSlots(children);

    return (
        <div className="w-full flex flex-col items-center my-8 space-y-6">
            <div
                className="relative w-full max-w-[32rem] aspect-[3/2] cursor-pointer group"
                style={{ perspective: "1500px" }}
                onClick={() => setIsFlipped(!isFlipped)}
            >
                <div
                    className={`absolute inset-0 w-full h-full transition-all duration-[800ms] ease-[cubic-bezier(0.23,1,0.32,1)] shadow-xl rounded-3xl ${isFlipped ? "[transform:rotateY(180deg)]" : ""}`}
                    style={{ transformStyle: "preserve-3d" }}
                >
                    {/* Front Face */}
                    <div
                        className="absolute inset-0 w-full h-full rounded-3xl bg-gradient-to-br from-[#162236] to-[#0f1a2b] border border-[#1e3a5f]/30 flex flex-col p-6 shadow-[0_10px_40px_rgba(15,26,43,0.3)] hover:border-[#c9a84c]/30 transition-colors"
                        style={{ backfaceVisibility: "hidden" }}
                    >
                        <div className="flex justify-between items-center mb-4">
                            <span className="text-[10px] uppercase font-bold tracking-widest text-[#c9a84c] opacity-80 bg-[#c9a84c]/10 px-2 py-1 rounded-md">
                                Flashcard
                            </span>
                            <svg className="w-4 h-4 text-[#c9a84c]/40 opacity-50 group-hover:opacity-100 transition-opacity shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                            </svg>
                        </div>
                        <div className="flex-1 flex items-center justify-center text-center overflow-y-auto custom-scrollbar">
                            <div className="text-lg md:text-xl lg:text-2xl font-semibold text-white leading-relaxed tracking-wide drop-shadow-md pb-4">
                                {frontContent.length > 0 ? frontContent : <span className="text-[#c8c3b8]/40 italic">Front Side</span>}
                            </div>
                        </div>
                        <div className="mt-4 text-center">
                            <span className="text-[11px] uppercase tracking-wider text-[#c8c3b8]/40 group-hover:text-[#c9a84c]/70 transition-colors">Click to flip</span>
                        </div>
                    </div>

                    {/* Back Face */}
                    <div
                        className="absolute inset-0 w-full h-full rounded-3xl bg-gradient-to-br from-[#1e3a5f] to-[#0f2847] border border-[#c9a84c]/25 flex flex-col p-6 shadow-[0_0_50px_rgba(201,168,76,0.1)] [transform:rotateY(180deg)]"
                        style={{ backfaceVisibility: "hidden" }}
                    >
                        <div className="flex justify-between items-center mb-4">
                            <span className="text-[10px] uppercase font-bold tracking-widest text-[#c9a84c] opacity-80 bg-[#c9a84c]/10 px-2 py-1 rounded-md">
                                Answer
                            </span>
                        </div>
                        <div className="flex-1 flex items-center justify-center text-center overflow-y-auto custom-scrollbar">
                            <div className="text-base md:text-lg lg:text-xl font-medium text-[#f0ede6] leading-relaxed pb-4">
                                {backContent.length > 0 ? backContent : <span className="text-[#c8c3b8]/40 italic">Back Side</span>}
                            </div>
                        </div>
                        <div className="mt-4 text-center">
                            <div className="inline-flex items-center justify-center gap-1.5 text-[#c9a84c]/50">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                                </svg>
                                <span className="text-[11px] uppercase tracking-wider">Flip back</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions */}
            {onPublish && (
                <div className="flex justify-center -mt-2">
                    <button
                        onClick={onPublish}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1e3a5f]/10 hover:bg-[#1e3a5f]/20 dark:bg-[#c9a84c]/10 dark:hover:bg-[#c9a84c]/20 border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 text-[#1e3a5f] dark:text-[#c9a84c] hover:text-[#1e3a5f] dark:hover:text-[#d4af37] text-xs font-bold transition-all shadow-sm"
                    >
                        <span>🌍</span> Publish to Community
                    </button>
                </div>
            )}

            {/* Hinds */}
            {hindsContent.length > 0 && (
                <div className="w-full max-w-[32rem] px-5 py-3.5 rounded-2xl bg-[#c9a84c]/5 border border-[#c9a84c]/15 text-sm text-[#1e3a5f] dark:text-[#c8c3b8] backdrop-blur-md flex items-start gap-3 shadow-lg transform -translate-y-2 animate-fade-in">
                    <div className="p-1.5 rounded-full bg-[#c9a84c]/15 text-[#c9a84c] mt-0.5">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                    </div>
                    <div className="leading-relaxed flex-1 pt-0.5">
                        {hindsContent}
                    </div>
                </div>
            )}
        </div>
    );
}
