import { authConfig, passwordMatches, safeNextPath, signSession, verifySession } from "./session";

const secret = "s".repeat(32);

describe("session", () => {
  it("accepts its own signature until expiry", () => {
    const now = Date.now();
    const value = signSession(secret, now);

    expect(verifySession(secret, value, now)).toBe(true);
    expect(verifySession(secret, value, now + 8 * 24 * 60 * 60 * 1000)).toBe(false);
  });

  it("rejects tampered, foreign, and malformed values", () => {
    const value = signSession(secret);
    const [expiresAt, signature] = value.split(".");

    expect(verifySession(secret, `${Number(expiresAt) + 1}.${signature}`)).toBe(false);
    expect(verifySession("o".repeat(32), value)).toBe(false);
    expect(verifySession(secret, "garbage")).toBe(false);
    expect(verifySession(secret, undefined)).toBe(false);
  });

  it("checks the password", () => {
    const config = { password: "correct horse", secret };
    expect(passwordMatches(config, "correct horse")).toBe(true);
    expect(passwordMatches(config, "correct hors")).toBe(false);
  });

  it("is disabled without a password and refuses a weak secret", () => {
    expect(authConfig({})).toBeNull();
    expect(() => authConfig({ OPERATOR_PASSWORD: "x", SESSION_SECRET: "short" })).toThrow(/SESSION_SECRET/);
  });

  it("only redirects to same-site paths", () => {
    expect(safeNextPath("/opportunities/1")).toBe("/opportunities/1");
    expect(safeNextPath("//evil.example")).toBe("/");
    expect(safeNextPath("https://evil.example")).toBe("/");
    expect(safeNextPath("/\\evil.example")).toBe("/");
    expect(safeNextPath(null)).toBe("/");
  });
});
