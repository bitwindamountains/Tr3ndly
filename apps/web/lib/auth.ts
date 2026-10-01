import { cookies } from "next/headers";

import { authConfig, SESSION_COOKIE, verifySession } from "./session";

export async function isOperator(): Promise<boolean> {
  const config = authConfig();
  if (!config) return true;
  const cookieStore = await cookies();
  return verifySession(config.secret, cookieStore.get(SESSION_COOKIE)?.value);
}

/** Server Functions are reachable by direct POST, so every one must call this first. */
export async function assertOperator(): Promise<void> {
  if (!(await isOperator())) throw new Error("Unauthorized");
}
