"use client";

import { useEffect, useState } from "react";
import { useTheme } from "./theme-provider";

export function ThemeToggle() {
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);

    // Avoid hydration mismatch by only rendering after mount
    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return <div className="h-[38px] w-[72px] opacity-0" aria-hidden="true" />;
    }

    return (
        <div className="relative inline-flex items-center bg-white/80 dark:bg-white/10 backdrop-blur-xl p-1 rounded-full space-x-1 shadow-sm border border-[#1e3a5f]/10 dark:border-[#c9a84c]/10 transition-all duration-300">
            <button
                type="button"
                onClick={() => setTheme("light")}
                className={`flex items-center justify-center p-1.5 rounded-full text-sm font-medium transition-all duration-300 ${theme === "light"
                    ? "bg-[#c9a84c]/15 text-[#8b6914] shadow-sm scale-100"
                    : "text-[#1e3a5f]/50 hover:text-[#1e3a5f] dark:text-[#c8c3b8]/50 dark:hover:text-[#c8c3b8] scale-95"
                    }`}
                aria-label="Light Mode"
                title="Light Mode"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-sun"><circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" /></svg>
            </button>

            <button
                type="button"
                onClick={() => setTheme("dark")}
                className={`flex items-center justify-center p-1.5 rounded-full text-sm font-medium transition-all duration-300 ${theme === "dark"
                    ? "bg-[#1e3a5f] text-white shadow-sm scale-100"
                    : "text-[#1e3a5f]/50 hover:text-[#1e3a5f] dark:text-[#c8c3b8]/50 dark:hover:text-[#c8c3b8] scale-95"
                    }`}
                aria-label="Dark Mode"
                title="Dark Mode"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-moon"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" /></svg>
            </button>
        </div>
    );
}

