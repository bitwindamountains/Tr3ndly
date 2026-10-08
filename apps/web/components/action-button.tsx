"use client";

import { useState, useTransition } from "react";

import type { ActionResult } from "@/app/actions";

/** Runs a bound Server Action and shows its result message. */
export function ActionButton({
  action,
  label,
  pendingLabel = "Working…",
  className = "button",
  disabled = false,
}: {
  action: () => Promise<ActionResult>;
  label: string;
  pendingLabel?: string;
  className?: string;
  disabled?: boolean;
}) {
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<ActionResult | null>(null);

  function run() {
    setResult(null);
    startTransition(async () => {
      try {
        setResult(await action());
      } catch {
        setResult({ ok: false, message: "Your session has expired. Sign in again." });
      }
    });
  }

  return (
    <span className="action-button">
      <button className={className} disabled={disabled || isPending} onClick={run} type="button">
        {isPending ? pendingLabel : label}
      </button>
      {result && (
        <span className={result.ok ? "form-success" : "form-error"} role="status">
          {result.message}
        </span>
      )}
    </span>
  );
}

export function FormMessage({ state }: { state: ActionResult | null }) {
  if (!state) return null;
  return (
    <div className={state.ok ? "form-success" : "form-error"} role="status">
      <p>{state.message}</p>
      {state.details && state.details.length > 0 && (
        <ul>{state.details.map((detail) => <li key={detail}>{detail}</li>)}</ul>
      )}
    </div>
  );
}
