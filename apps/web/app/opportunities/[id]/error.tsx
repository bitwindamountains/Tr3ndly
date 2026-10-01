"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function OpportunityError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="shell error-state">
      <h1>Could not load this opportunity</h1>
      <p>The Tr3ndly API did not respond. Check that it is running, then try again.</p>
      <button onClick={() => retry()} type="button">Try again</button>
      <Link href="/">Back to Today</Link>
    </main>
  );
}
