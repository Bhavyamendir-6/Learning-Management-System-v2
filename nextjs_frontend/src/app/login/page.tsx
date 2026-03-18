"use client";

import { useState } from "react";
import { fetchAPI, setToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function Login() {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            if (isLogin) {
                const data = await fetchAPI("/auth/login", {
                    method: "POST",
                    body: JSON.stringify({ username, password }),
                });
                setToken(data.access_token);
                router.push("/");
            } else {
                await fetchAPI("/auth/signup", {
                    method: "POST",
                    body: JSON.stringify({ username, email, password }),
                });
                setIsLogin(true);
                setError("Account created! You can now log in.");
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--bg-color)]">
            <div className="glass w-full max-w-md p-8 rounded-2xl shadow-xl animate-slide-up">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-[#1e3a5f] to-[#c9a84c] bg-clip-text text-transparent text-center mb-6" style={{ fontFamily: 'var(--font-serif)' }}>
                    LMS Agent
                </h1>

                <h2 className="text-xl font-semibold mb-6 text-center text-[#1e3a5f] dark:text-[#e8e4db]">
                    {isLogin ? "Welcome back" : "Create an account"}
                </h2>

                {error && (
                    <div className={`p-3 rounded-lg mb-6 text-sm ${error.includes("created") ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"}`}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1 text-[#1e3a5f] dark:text-[#c8c3b8]">Username</label>
                        <input
                            type="text"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-2 rounded-lg border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 bg-white dark:bg-[#0a1220]/70 text-[#1e3a5f] dark:text-[#e8e4db] focus:ring-2 focus:ring-[#c9a84c]/40 outline-none transition-shadow"
                        />
                    </div>

                    {!isLogin && (
                        <div>
                            <label className="block text-sm font-medium mb-1 text-[#1e3a5f] dark:text-[#c8c3b8]">Email</label>
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-2 rounded-lg border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 bg-white dark:bg-[#0a1220]/70 text-[#1e3a5f] dark:text-[#e8e4db] focus:ring-2 focus:ring-[#c9a84c]/40 outline-none transition-shadow"
                            />
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium mb-1 text-[#1e3a5f] dark:text-[#c8c3b8]">Password</label>
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 rounded-lg border border-[#1e3a5f]/15 dark:border-[#c9a84c]/15 bg-white dark:bg-[#0a1220]/70 text-[#1e3a5f] dark:text-[#e8e4db] focus:ring-2 focus:ring-[#c9a84c]/40 outline-none transition-shadow"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2.5 rounded-lg bg-[#1e3a5f] hover:bg-[#173050] text-white font-medium shadow-md shadow-[#1e3a5f]/20 transition-all active:scale-[0.98] disabled:opacity-70 disabled:active:scale-100 mt-6"
                    >
                        {loading ? "Please wait..." : isLogin ? "Sign In" : "Sign Up"}
                    </button>
                </form>

                <div className="mt-6 text-center text-sm text-[#1e3a5f]/50 dark:text-[#c8c3b8]/50">
                    {isLogin ? "Don't have an account? " : "Already have an account? "}
                    <button
                        onClick={() => {
                            setIsLogin(!isLogin);
                            setError("");
                        }}
                        className="text-[#c9a84c] hover:text-[#d4af37] font-medium"
                    >
                        {isLogin ? "Sign up" : "Log in"}
                    </button>
                </div>
            </div>
        </div>
    );
}
