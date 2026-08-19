"use client";

import { signOut } from "next-auth/react";

export default function LogoutButton() {
  return (
    <button
      type="button"
      onClick={() =>
        signOut({
          callbackUrl: "/login",
        })
      }
      className="rounded-xl border border-[#252B45] bg-[#11172D] px-4 py-2 text-sm font-medium text-[#A7AEC4] transition hover:border-[#5546E8]/50 hover:bg-[#5546E8]/10 hover:text-white"
    >
      Logout
    </button>
  );
}