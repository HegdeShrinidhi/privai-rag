import { auth } from "@/auth";

export async function GET() {
  const session = await auth();

  if (!session?.user?.email) {
    return Response.json(
      {
        authenticated: false,
      },
      {
        status: 401,
      }
    );
  }

  return Response.json({
    authenticated: true,
    user: {
      email: session.user.email,
      name: session.user.name,
      image: session.user.image,
    },
  });
}