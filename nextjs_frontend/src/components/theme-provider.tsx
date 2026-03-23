"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

type Theme = "dark" | "light" | "system";

type ThemeProviderProps = {
    children: React.ReactNode;
    defaultTheme?: Theme;
    storageKey?: string;
};

type ThemeProviderState = {
    theme: Theme;
    resolvedTheme: "dark" | "light";
    setTheme: (theme: Theme) => void;
};

const initialState: ThemeProviderState = {
    theme: "system",
    resolvedTheme: "dark",
    setTheme: () => null,
};

const ThemeProviderContext = createContext<ThemeProviderState>(initialState);

function getSystemTheme(): "dark" | "light" {
    if (typeof window === "undefined") return "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme: Theme) {
    const root = window.document.documentElement;
    const resolved = theme === "system" ? getSystemTheme() : theme;

    // Remove both classes first, then add the resolved one
    root.classList.remove("light", "dark");
    root.classList.add(resolved);
    root.style.colorScheme = resolved;

    return resolved;
}

export function ThemeProvider({
    children,
    defaultTheme = "system",
    storageKey = "theme",
}: ThemeProviderProps) {
    const [theme, setThemeState] = useState<Theme>(() => {
        if (typeof window === "undefined") return defaultTheme;
        return (localStorage.getItem(storageKey) as Theme) || defaultTheme;
    });

    const [resolvedTheme, setResolvedTheme] = useState<"dark" | "light">(() => {
        if (typeof window === "undefined") return "dark";
        return theme === "system" ? getSystemTheme() : (theme as "dark" | "light");
    });

    // Apply theme whenever it changes
    useEffect(() => {
        const resolved = applyTheme(theme);
        setResolvedTheme(resolved);
    }, [theme]);

    // Listen for OS theme changes when in "system" mode
    useEffect(() => {
        if (theme !== "system") return;

        const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        const handler = () => {
            const resolved = applyTheme("system");
            setResolvedTheme(resolved);
        };

        mediaQuery.addEventListener("change", handler);
        return () => mediaQuery.removeEventListener("change", handler);
    }, [theme]);

    const setTheme = useCallback((newTheme: Theme) => {
        localStorage.setItem(storageKey, newTheme);
        setThemeState(newTheme);
    }, [storageKey]);

    const value = {
        theme,
        resolvedTheme,
        setTheme,
    };

    return (
        <ThemeProviderContext.Provider value={value}>
            {children}
        </ThemeProviderContext.Provider>
    );
}

export const useTheme = () => {
    const context = useContext(ThemeProviderContext);

    if (context === undefined)
        throw new Error("useTheme must be used within a ThemeProvider");

    return context;
};
