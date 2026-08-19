"use client";

import { signIn } from "next-auth/react";
import { useState } from "react";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);

  async function handleGoogleLogin() {
    try {
      setLoading(true);

      await signIn("google", {
        callbackUrl: "/",
      });
    } catch (error) {
      console.error("Google sign-in failed:", error);
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#080C1C] text-white">

      <div className="grid min-h-screen lg:grid-cols-2">

        {/* ================================================== */}
        {/* LEFT SIDE - PRIVAI-RAG BRANDING */}
        {/* ================================================== */}

        <section className="relative hidden overflow-hidden lg:flex">

          {/* Background glow */}

          <div className="absolute -left-32 top-20 h-[500px] w-[500px] rounded-full bg-[#5546E8]/20 blur-[120px]" />

          <div className="absolute bottom-0 right-0 h-[400px] w-[400px] rounded-full bg-[#2563EB]/10 blur-[120px]" />


          {/* Decorative shapes */}

          {/* <div className="absolute left-10 top-24 h-20 w-20 rounded-3xl border border-[#5546E8]/20 bg-[#5546E8]/5" />

          <div className="absolute bottom-24 left-24 h-32 w-32 rounded-full border border-[#5546E8]/10" />

          <div className="absolute right-16 top-16 h-24 w-24 rounded-3xl bg-[#5546E8]/10 blur-sm" /> */}


          <div className="relative z-10 flex w-full flex-col justify-between p-12 xl:p-16">

            {/* Logo */}

            <div className="flex items-center gap-3">

              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#5546E8] text-xl shadow-lg shadow-[#5546E8]/30">

                ✦

              </div>

              <div>

                <h1 className="text-lg font-semibold">
                  PrivAI-RAG
                </h1>

                <p className="text-xs text-[#69728D]">
                  Enterprise Document Intelligence
                </p>

              </div>

            </div>


            {/* Main content */}

            <div className="max-w-xl">

              {/* Security badge */}

              <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#5546E8]/30 bg-[#5546E8]/10 px-4 py-2 text-xs font-medium text-[#8B87FF]">

                <span className="h-2 w-2 rounded-full bg-[#22C55E] shadow-[0_0_8px_#22C55E]" />

                PRIVATE AI • SECURE BY DESIGN

              </div>


              {/* Heading */}

              <h2 className="text-5xl font-bold leading-[1.05] tracking-tight xl:text-6xl">

                Your knowledge.

                <br />

                <span className="gradient-text">
                  Your privacy.
                </span>

              </h2>


              <p className="mt-7 max-w-lg text-lg leading-8 text-[#A7AEC4]">

                Securely upload enterprise documents,
                search your private knowledge base,
                and get grounded answers with AI.

              </p>


              {/* Feature cards */}

              <div className="mt-10 grid grid-cols-3 gap-3">

                {/* Card 1 */}

                <div className="rounded-2xl border border-[#252B45] bg-[#11172D]/70 p-4 backdrop-blur-xl">

                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-[#5546E8]/15 text-lg">

                    🔐

                  </div>

                  <p className="text-sm font-medium">
                    Private
                  </p>

                  <p className="mt-1 text-xs leading-5 text-[#69728D]">
                    User-isolated data
                  </p>

                </div>


                {/* Card 2 */}

                <div className="rounded-2xl border border-[#252B45] bg-[#11172D]/70 p-4 backdrop-blur-xl">

                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-[#2563EB]/15 text-lg">

                    🧠

                  </div>

                  <p className="text-sm font-medium">
                    Grounded
                  </p>

                  <p className="mt-1 text-xs leading-5 text-[#69728D]">
                    Context-aware AI
                  </p>

                </div>


                {/* Card 3 */}

                <div className="rounded-2xl border border-[#252B45] bg-[#11172D]/70 p-4 backdrop-blur-xl">

                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-[#22C55E]/10 text-lg">

                    ✓

                  </div>

                  <p className="text-sm font-medium">
                    Reliable
                  </p>

                  <p className="mt-1 text-xs leading-5 text-[#69728D]">
                    Source-backed answers
                  </p>

                </div>

              </div>

            </div>


            {/* Footer */}

            <div className="flex items-center justify-between text-xs text-[#4E5875]">

              <span>
                Private • Grounded • Enterprise AI
              </span>

              <span>
                PrivAI-RAG
              </span>

            </div>

          </div>

        </section>


        {/* ================================================== */}
        {/* RIGHT SIDE - LOGIN */}
        {/* ================================================== */}

        <section className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 py-12">

          {/* Mobile background glow */}

          <div className="pointer-events-none absolute left-1/2 top-0 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-[#5546E8]/10 blur-[120px]" />


          <div className="relative z-10 w-full max-w-md">

            {/* Mobile logo */}

            <div className="mb-10 flex items-center justify-center gap-3 lg:hidden">

              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#5546E8] text-xl shadow-lg shadow-[#5546E8]/30">

                ✦

              </div>

              <div>

                <h1 className="text-lg font-semibold">
                  PrivAI-RAG
                </h1>

                <p className="text-xs text-[#69728D]">
                  Enterprise Document Intelligence
                </p>

              </div>

            </div>


            {/* Login card */}

            <div className="rounded-3xl border border-[#252B45] bg-[#0D1226]/90 p-8 shadow-2xl shadow-black/30 backdrop-blur-xl sm:p-10">

              {/* Icon */}

              <div className="mb-8 flex justify-center">

                <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-[#5546E8]/20 bg-[#5546E8]/10 text-3xl">

                  🔐

                </div>

              </div>


              {/* Heading */}

              <div className="text-center">

                <p className="mb-3 text-xs font-semibold tracking-[0.2em] text-[#6C63FF]">

                  SECURE ACCESS

                </p>

                <h2 className="text-3xl font-bold tracking-tight">

                  Welcome to PrivAI-RAG

                </h2>

                <p className="mx-auto mt-3 max-w-sm text-sm leading-6 text-[#69728D]">

                  Sign in to access your private
                  enterprise knowledge workspace.

                </p>

              </div>


              {/* Divider */}

              <div className="my-8 flex items-center gap-4">

                <div className="h-px flex-1 bg-[#252B45]" />

                <span className="text-xs text-[#4E5875]">
                  SECURE LOGIN
                </span>

                <div className="h-px flex-1 bg-[#252B45]" />

              </div>


              {/* Google login */}

              <button
                type="button"
                onClick={handleGoogleLogin}
                disabled={loading}
                className="
                  flex
                  w-full
                  items-center
                  justify-center
                  gap-3
                  rounded-xl
                  border
                  border-[#252B45]
                  bg-white
                  px-5
                  py-3.5
                  text-sm
                  font-semibold
                  text-[#111827]
                  transition
                  duration-200
                  hover:bg-[#F3F4F6]
                  hover:shadow-lg
                  disabled:cursor-not-allowed
                  disabled:opacity-60
                "
              >

                {/* Google logo */}

                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >

                  <path
                    d="M21.35 12.23c0-.72-.06-1.42-.18-2.09H12v3.96h5.23a4.47 4.47 0 0 1-1.94 2.93v2.44h3.14c1.84-1.7 2.92-4.2 2.92-7.24Z"
                    fill="#4285F4"
                  />

                  <path
                    d="M12 21.66c2.63 0 4.84-.87 6.45-2.36l-3.14-2.44c-.87.58-1.98.92-3.31.92-2.54 0-4.69-1.72-5.46-4.03H3.3v2.52A9.74 9.74 0 0 0 12 21.66Z"
                    fill="#34A853"
                  />

                  <path
                    d="M6.54 13.75a5.85 5.85 0 0 1 0-3.5V7.73H3.3a9.74 9.74 0 0 0 0 8.54l3.24-2.52Z"
                    fill="#FBBC05"
                  />

                  <path
                    d="M12 6.22c1.43 0 2.72.49 3.73 1.45l2.8-2.8C16.84 3.28 14.63 2.34 12 2.34a9.74 9.74 0 0 0-8.7 5.39l3.24 2.52C7.31 7.94 9.46 6.22 12 6.22Z"
                    fill="#EA4335"
                  />

                </svg>


                {loading
                  ? "Signing you in..."
                  : "Continue with Google"}

              </button>


              {/* Security information */}

              <div className="mt-7 rounded-2xl border border-[#252B45] bg-[#11172D]/70 p-4">

                <div className="flex gap-3">

                  <div className="mt-0.5 text-base">
                    🛡️
                  </div>

                  <div>

                    <p className="text-xs font-semibold text-[#A7AEC4]">
                      Your data stays isolated
                    </p>

                    <p className="mt-1 text-xs leading-5 text-[#69728D]">

                      Documents and AI retrieval are
                      scoped to your authenticated
                      account.

                    </p>

                  </div>

                </div>

              </div>


              {/* Terms */}

              <p className="mt-7 text-center text-xs leading-5 text-[#4E5875]">

                By continuing, you agree to use
                PrivAI-RAG responsibly and securely.

              </p>

            </div>


            {/* Bottom status */}

            <div className="mt-6 flex items-center justify-center gap-2 text-xs text-[#4E5875]">

              <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />

              Secure authentication

              <span className="text-[#252B45]">
                •
              </span>

              Google OAuth

            </div>

          </div>

        </section>

      </div>

    </main>
  );
}