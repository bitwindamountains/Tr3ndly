"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type DecisionValue = "accepted" | "rejected" | "deferred" | "insufficient_evidence";

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

export function DecisionPanel({ opportunityId }: { opportunityId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState<DecisionValue | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function decide(decision: DecisionValue, reasonCode: string) {
    setPending(decision);
    setMessage(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const response = await fetch(`${baseUrl}/opportunities/${opportunityId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, reason_code: reasonCode }),
      });
      if (!response.ok) throw new Error(`Decision failed with ${response.status}`);
      setMessage("Decision recorded.");
      router.refresh();
    } catch {
      setMessage("Could not record the decision. Check the API connection.");
    } finally {
      setPending(null);
    }
  }

  return (
    <section className="decision-panel" aria-labelledby="decision-heading">
      <p className="eyebrow">Operator decision</p>
      <h2 id="decision-heading">Is this worth a marketplace search?</h2>
      <p>Your response becomes labeled feedback for future recommendation quality.</p>
      <div className="decision-actions">
        {actions.map((action) => (
          <button
            className={`decision-${action.value}`}
            disabled={pending !== null}
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

