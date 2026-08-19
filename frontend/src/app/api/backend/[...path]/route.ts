import { auth } from "@/auth";
import { NextRequest } from "next/server";

const API_URL =
  process.env.BACKEND_API_URL ||
  "http://127.0.0.1:8000";

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

async function proxyRequest(
  request: NextRequest,
  context: RouteContext
) {
  // =========================================================
  // 1. Verify Auth.js session
  // =========================================================

  const session = await auth();

  if (!session?.user?.email) {
    return Response.json(
      {
        detail: "Authentication required.",
      },
      {
        status: 401,
      }
    );
  }

  // =========================================================
  // 2. Get requested backend path
  // =========================================================

  const { path } = await context.params;

  const backendPath =
    "/" + path.join("/");

  const search =
    request.nextUrl.search;

  const targetUrl =
    `${API_URL}${backendPath}${search}`;

  // =========================================================
  // 3. Copy request headers
  // =========================================================

  const headers = new Headers();

  const contentType =
    request.headers.get(
      "content-type"
    );

  if (contentType) {
    headers.set(
      "content-type",
      contentType
    );
  }

  // =========================================================
  // 4. Add verified user identity
  //
  // IMPORTANT:
  //
  // The browser does NOT supply X-User-ID.
  //
  // The server gets the email from Auth.js.
  // =========================================================

  headers.set(
    "X-User-ID",
    session.user.email
  );

  // =========================================================
  // 5. Prepare request body
  // =========================================================

  let body: BodyInit | undefined;

  if (
    request.method !== "GET" &&
    request.method !== "HEAD"
  ) {
    body = await request.arrayBuffer();
  }

  // =========================================================
  // 6. Forward request to FastAPI
  // =========================================================

  try {
    const response = await fetch(
      targetUrl,
      {
        method: request.method,

        headers,

        body,

        cache: "no-store",
      }
    );

    // =======================================================
    // 7. Forward response
    // =======================================================

    const responseBody =
      await response.arrayBuffer();

    const responseHeaders =
      new Headers();

    const responseContentType =
      response.headers.get(
        "content-type"
      );

    if (responseContentType) {
      responseHeaders.set(
        "content-type",
        responseContentType
      );
    }

    return new Response(
      responseBody,
      {
        status: response.status,

        headers:
          responseHeaders,
      }
    );
  } catch (error) {
    console.error(
      "Backend proxy error:",
      error
    );

    return Response.json(
      {
        detail:
          "Unable to connect to backend.",
      },
      {
        status: 502,
      }
    );
  }
}

// ============================================================
// HTTP Methods
// ============================================================

export async function GET(
  request: NextRequest,
  context: RouteContext
) {
  return proxyRequest(
    request,
    context
  );
}

export async function POST(
  request: NextRequest,
  context: RouteContext
) {
  return proxyRequest(
    request,
    context
  );
}

export async function DELETE(
  request: NextRequest,
  context: RouteContext
) {
  return proxyRequest(
    request,
    context
  );
}

export async function PUT(
  request: NextRequest,
  context: RouteContext
) {
  return proxyRequest(
    request,
    context
  );
}

export async function PATCH(
  request: NextRequest,
  context: RouteContext
) {
  return proxyRequest(
    request,
    context
  );
}