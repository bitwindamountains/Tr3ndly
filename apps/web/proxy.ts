import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { authConfig, SESSION_COOKIE, verifySession } from "./lib/session";

/** Send visitors without a valid operator session to /login. Server actions re-check. */
export function proxy(request: NextRequest) {
  const config = authConfig();
  if (!config || request.nextUrl.pathname === "/login") return NextResponse.next();

  if (verifySession(config.secret, request.cookies.get(SESSION_COOKIE)?.value)) {
    return NextResponse.next();
  }
  const login = new URL("/login", request.url);
  login.searchParams.set("next", request.nextUrl.pathname + request.nextUrl.search);
  return NextResponse.redirect(login);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
