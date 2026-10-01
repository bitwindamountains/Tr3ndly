"use client";

import { useActionState } from "react";

import { login } from "@/app/actions";

export function LoginForm({ next }: { next: string }) {
  const [state, action, pending] = useActionState(login, null);

  return (
    <form action={action} className="login-form">
      <input name="next" type="hidden" value={next} />
      <label htmlFor="password">Operator password</label>
      <input autoComplete="current-password" autoFocus id="password" name="password" required type="password" />
      <button disabled={pending} type="submit">{pending ? "Signing in…" : "Sign in"}</button>
      {state && !state.ok && <p className="login-error" role="alert">{state.message}</p>}
    </form>
  );
}
