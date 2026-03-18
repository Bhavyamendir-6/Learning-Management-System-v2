"use client";

import React, { useRef, useState } from "react";

interface PdfUploaderProps {
    onUpload: (file: File) => void;
    isUploading: boolean;
}

export default function PdfUploader({ onUpload, isUploading }: PdfUploaderProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [dragActive, setDragActive] = useState(false);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            if (file.type === "application/pdf") {
                onUpload(file);
            }
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            onUpload(e.target.files[0]);
        }
    };

    return (
        <div
            className={`relative w-full border-2 border-dashed rounded-xl p-6 transition-all duration-200 ease-in-out flex flex-col items-center justify-center text-center cursor-pointer overflow-hidden ${dragActive
                ? "border-[#c9a84c] bg-[#c9a84c]/10 dark:bg-[#c9a84c]/10 shadow-inner"
                : "border-[#1e3a5f]/20 dark:border-[#c9a84c]/20 hover:bg-[#1e3a5f]/3 dark:hover:bg-[#c9a84c]/5 hover:border-[#c9a84c]/50 dark:hover:border-[#c9a84c]/40"
                }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                onChange={handleChange}
                className="hidden"
            />

            {isUploading ? (
                <div className="flex flex-col items-center animate-pulse">
                    <div className="w-10 h-10 border-4 border-[#c9a84c]/30 border-t-[#c9a84c] rounded-full animate-spin mb-3"></div>
                    <p className="text-sm font-medium text-[#1e3a5f] dark:text-[#c9a84c]">
                        Uploading & indexing PDF...
                    </p>
                </div>
            ) : (
                <>
                    <svg
                        className={`w-12 h-12 mb-3 transition-colors ${dragActive ? "text-[#c9a84c]" : "text-[#1e3a5f]/30 dark:text-[#c9a84c]/40"
                            }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <h3 className="text-base font-semibold text-[#1e3a5f] dark:text-[#e8e4db] mb-1">
                        Upload PDF Document
                    </h3>
                    <p className="text-xs text-[#1e3a5f]/50 dark:text-[#c8c3b8]/60 max-w-xs">
                        Drag & drop your PDF here, or click to browse. Let the AI tutor help you!
                    </p>
                </>
            )}
        </div>
    );
}
