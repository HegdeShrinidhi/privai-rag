import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const {
  handlers,
  auth,
  signIn,
  signOut,
} = NextAuth({
  providers: [
    Google({
      clientId:
        process.env.AUTH_GOOGLE_ID,

      clientSecret:
        process.env.AUTH_GOOGLE_SECRET,
    }),
  ],

  pages: {
    signIn: "/login",
  },

  session: {
    strategy: "jwt",
  },

  callbacks: {
    async jwt({
      token,
      profile,
    }) {
      if (profile?.email) {
        token.email = profile.email;
      }

      return token;
    },

    async session({
      session,
      token,
    }) {
      if (session.user) {
        session.user.email =
          token.email as string;
      }

      return session;
    },
  },
});