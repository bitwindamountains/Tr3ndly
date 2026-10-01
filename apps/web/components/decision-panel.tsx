"use client";

import { useState, useTransition } from "react";

import { recordDecision } from "@/app/actions";
import type { Decision } from "@/lib/types";

type DecisionValue = Decision["decision"];

const actions: Array<{ value: DecisionValue; label: string; reason: string }> = [
  { value: "accepted", label: "Accept", reason: "useful_opportunity" },
  { value: "deferred", label: "Defer", reason: "review_later" },
  { value: "rejected", label: "Reject", reason: "not_a_fit" },
  {
    value: "insufficient_evidence",
    label: "Needs evidence",
    reason: "insufficient_evidence",
  },
];

export function DecisionPanel({ opportunityId, closed }: { opportunityId: string; closed: boolean }) {
  const [isPending, startTransition] = useTransition();
  const [pending, setPending] = useState<DecisionValue | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  function decide(decision: DecisionValue, reasonCode: string) {
    setPending(decision);
    setMessage(null);
    startTransition(async () => {
      try {
        const result = await recordDecision(opportunityId, decision, reasonCode);
        setMessage(result.message);
      } catch {
        setMessage("Your session has expired. Sign in again to record decisions.");
      } finally {
        setPending(null);
      }
    });
  }

  return (
    <section className="decision-panel" aria-labelledby="decision-heading">
      <p className="eyebrow">Operator decision</p>
      <h2 id="decision-heading">Is this worth a marketplace search?</h2>
      <p>
        {closed
          ? "This opportunity is closed to new decisions."
          : "Your response becomes labeled feedback for future recommendation quality."}
      </p>
      <div className="decision-actions">
        {actions.map((action) => (
          <button
            className={`decision-${action.value}`}
            disabled={closed || isPending}
            key={action.value}
            onClick={() => decide(action.value, action.reason)}
            type="button"
          >
            {pending === action.value ? "Saving…" : action.label}
          </button>
        ))}
      </div>
      {message && <p className="decision-message" role="status">{message}</p>}
    </section>
  );
}
