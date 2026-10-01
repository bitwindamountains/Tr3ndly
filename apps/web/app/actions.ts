"use server";

import { refresh } from "next/cache";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { postDecision } from "@/lib/api";
import { assertOperator } from "@/lib/auth";
import {
  authConfig,
  passwordMatches,
  safeNextPath,
  SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
  signSession,
} from "@/lib/session";
import type { Decision } from "@/lib/types";

const DECISIONS: ReadonlyArray<Decision["decision"]> = [
  "accepted",
  "rejected",
  "deferred",
  "insufficient_evidence",
];

export type ActionResult = { ok: boolean; message: string };

export async function recordDecision(
  opportunityId: string,
  decision: Decision["decision"],
  reasonCode: string,
): Promise<ActionResult> {
  await assertOperator();
  if (!DECISIONS.includes(decision) || !/^[a-z_]{2,120}$/.test(reasonCode)) {
    return { ok: false, message: "Invalid decision." };
  }
  try {
    const result = await postDecision(opportunityId, decision, reasonCode);
    if (!result.ok) {
      return { ok: false, message: result.status === 409 ? result.detail : "Could not record the decision." };
    }
  } catch {
    return { ok: false, message: "Could not reach the Tr3ndly API." };
  }
  refresh();
  return { ok: true, message: "Decision recorded." };
}

export async function login(_previous: ActionResult | null, formData: FormData): Promise<ActionResult> {
  const config = authConfig();
  const next = safeNextPath(formData.get("next"));
  if (config) {
    const password = formData.get("password");
    if (typeof password !== "string" || !passwordMatches(config, password)) {
      return { ok: false, message: "Incorrect password." };
    }
    const cookieStore = await cookies();
    cookieStore.set(SESSION_COOKIE, signSession(config.secret), {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: SESSION_MAX_AGE_SECONDS,
    });
  }
  redirect(next);
}

export async function logout(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE);
  redirect("/login");
}
