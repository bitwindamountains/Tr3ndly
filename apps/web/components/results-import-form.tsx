"use client";

import { useActionState } from "react";

import { importResults } from "@/app/actions";
import { FormMessage } from "./action-button";

export function ResultsImportForm() {
  const [state, action, pending] = useActionState(importResults, null);

  return (
    <form action={action} className="stack-form">
      <label>
        Affiliate report (CSV)
        <input accept=".csv,text/csv" name="file" type="file" />
      </label>
      <label>
        Or paste rows
        <textarea
          name="csv"
          placeholder={"sub_id,date,views,clicks,orders,gmv,commission\nt3a1b2c3d4,2026-10-09,5400,120,4,1396,118.64"}
          rows={4}
        />
      </label>
      <small>
        Needs a tracking code (or sub ID) column and a date column (YYYY-MM-DD or MM/DD/YYYY). Views, clicks, orders,
        GMV, and commission are optional. Codes Tr3ndly did not issue count as baseline posts.
      </small>
      <button className="button" disabled={pending} type="submit">{pending ? "Importing…" : "Import results"}</button>
      <FormMessage state={state} />
    </form>
  );
}
