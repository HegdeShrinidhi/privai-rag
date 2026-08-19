"use client";

import { signIn } from "next-auth/react";

export default function LoginPage() {

  async function handleGoogleLogin() {
    await signIn("google", {
      callbackUrl: "/",
    });
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#080C1C] px-6 text-white">

      <div className="w-full max-w-md">

        <div className="rounded-3xl border border-[#252B45] bg-[#11172D] p-8 shadow-2xl">

          {/* Logo */}

          <div className="flex justify-center">

            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#5546E8] text-2xl shadow-lg shadow-[#5546E8]/20">
              ✦
            </div>

          </div>


          {/* Heading */}

          <div className="mt-6 text-center">

            <h1 className="text-2xl font-bold">
              Welcome to PrivAI-RAG
            </h1>

            <p className="mt-2 text-sm text-[#69728D]">
              Private enterprise document intelligence
            </p>

          </div>


          {/* Google Login */}

          <button
            type="button"
            onClick={handleGoogleLogin}
            className="mt-8 flex w-full items-center justify-center gap-3 rounded-xl bg-white px-5 py-3.5 font-medium text-[#11172D] transition hover:bg-gray-100"
          >

            <span className="text-lg font-bold">
              G
            </span>

            Continue with Google

          </button>


          {/* Privacy message */}

          <p className="mt-6 text-center text-xs leading-5 text-[#4F5872]">
            Sign in to securely access your
            private document workspace.
          </p>

        </div>

      </div>

    </main>
  );
}