import { createHmac, timingSafeEqual } from "node:crypto";

/**
 * Single-operator sessions: an HMAC-signed expiry timestamp in an httpOnly cookie.
 *
 * Auth is enabled when OPERATOR_PASSWORD is set; SESSION_SECRET (32+ chars) signs the cookie.
 * Without OPERATOR_PASSWORD the web app is open, which is only acceptable for local development.
 */

export const SESSION_COOKIE = "tr3ndly_session";
export const SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;

export interface AuthConfig {
  password: string;
  secret: string;
}

export function authConfig(env: Record<string, string | undefined> = process.env): AuthConfig | null {
  const password = env.OPERATOR_PASSWORD;
  if (!password) return null;
  const secret = env.SESSION_SECRET ?? "";
  if (secret.length < 32) {
    throw new Error("SESSION_SECRET must be at least 32 characters when OPERATOR_PASSWORD is set");
  }
  return { password, secret };
}

export function signSession(secret: string, now = Date.now()): string {
  const expiresAt = String(now + SESSION_MAX_AGE_SECONDS * 1000);
  return `${expiresAt}.${digest(secret, expiresAt)}`;
}

export function verifySession(secret: string, value: string | undefined, now = Date.now()): boolean {
  if (!value) return false;
  const [expiresAt, signature] = value.split(".");
  if (!expiresAt || !signature || !/^\d+$/.test(expiresAt)) return false;
  if (!safeEqual(signature, digest(secret, expiresAt))) return false;
  return Number(expiresAt) > now;
}

export function passwordMatches(config: AuthConfig, candidate: string): boolean {
  // Compare fixed-length digests so neither length nor content leaks through timing.
  return safeEqual(digest(config.secret, candidate), digest(config.secret, config.password));
}

/** Only allow same-site relative redirects after login. */
export function safeNextPath(next: unknown): string {
  if (typeof next !== "string" || !next.startsWith("/") || next.startsWith("//") || next.includes("\\")) {
    return "/";
  }
  return next;
}

function digest(secret: string, value: string): string {
  return createHmac("sha256", secret).update(value).digest("base64url");
}

function safeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
}
