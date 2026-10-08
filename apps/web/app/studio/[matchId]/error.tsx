"use client";

import { useEffect } from "react";

export default function StudioError({
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
      <h1>Could not load the studio</h1>
      <p>The Tr3ndly API did not respond. Check that it is running, then try again.</p>
      <button onClick={() => retry()} type="button">Try again</button>
    </main>
  );
}
