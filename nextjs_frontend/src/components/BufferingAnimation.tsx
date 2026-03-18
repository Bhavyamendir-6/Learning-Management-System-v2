"use client";

import React from "react";

interface BufferingAnimationProps {
    className?: string;
    size?: "sm" | "md" | "lg";
}

export default function BufferingAnimation({ className = "", size = "md" }: BufferingAnimationProps) {
    const sizeMap = {
        sm: "w-8 h-8",
        md: "w-16 h-16",
        lg: "w-24 h-24"
    };

    const containerSize = sizeMap[size];

    return (
        <div className={`relative flex items-center justify-center ${containerSize} ${className}`}>
            {/* Outer rhythmic breathing glow */}
            <div className="absolute inset-[-25%] rounded-full bg-gradient-to-tr from-[#1e3a5f]/30 via-[#c9a84c]/30 to-[#d4af37]/30 blur-xl animate-breathe-outer pointer-events-none"></div>

            {/* The primary magical ring with conic gradient and drop-shadows */}
            <div className="absolute inset-0 buffering-ring z-10 pointer-events-none"></div>

            {/* Inner counter-rotating ring for depth and complex movement */}
            <div className="absolute inset-[15%] buffering-ring-inner z-20 pointer-events-none"></div>

            {/* A sharp inner core glow point */}
            <div className="absolute w-1/5 h-1/5 bg-white rounded-full blur-[2px] animate-core-pulse z-30 pointer-events-none"></div>
        </div>
    );
}
