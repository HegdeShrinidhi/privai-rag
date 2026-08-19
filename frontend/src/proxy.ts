import { auth } from "@/auth";

export default auth((req) => {
  const isLoggedIn = !!req.auth;

  const isLoginPage =
    req.nextUrl.pathname === "/login";

  // Allow login page
  if (isLoginPage) {
    return;
  }

  // Redirect unauthenticated users
  if (!isLoggedIn) {
    const loginUrl = new URL(
      "/login",
      req.nextUrl.origin
    );

    loginUrl.searchParams.set(
      "callbackUrl",
      req.nextUrl.pathname
    );

    return Response.redirect(loginUrl);
  }
});

export const config = {
  matcher: [
    "/((?!api/auth|_next/static|_next/image|favicon.ico).*)",
  ],
};