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

      if (profile?.name) {
        token.name = profile.name;
      }

      if (profile?.picture) {
        token.picture = profile.picture;
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

        session.user.name =
          token.name as string;

        session.user.image =
          token.picture as string;
      }

      return session;
    },
  },
});