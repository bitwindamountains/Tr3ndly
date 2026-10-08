"use client";

import { useActionState } from "react";

import { addProductMatch, logSearchFailure } from "@/app/actions";
import { FormMessage } from "./action-button";

const MARKETPLACES = [
  ["shopee", "Shopee"],
  ["lazada", "Lazada"],
  ["tiktok_shop", "TikTok Shop"],
  ["other", "Other"],
] as const;

function MarketplaceSelect() {
  return (
    <label>
      Marketplace
      <select name="marketplace" required defaultValue="shopee">
        {MARKETPLACES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
    </label>
  );
}

/** Capture a real listing the operator found (plan section 12). */
export function ListingForm({ opportunityId }: { opportunityId: string }) {
  const [state, action, pending] = useActionState(addProductMatch.bind(null, opportunityId), null);

  return (
    <form action={action} className="stack-form">
      <div className="form-grid">
        <MarketplaceSelect />
        <label>
          Seller type
          <select name="seller_type" defaultValue="">
            <option value="">Unknown</option>
            <option value="mall">Mall / official store</option>
            <option value="preferred">Preferred seller</option>
            <option value="standard">Standard seller</option>
          </select>
        </label>
        <label className="span-2">Listing title<input name="listing_title" required minLength={3} maxLength={500} /></label>
        <label className="span-2">Product URL<input name="product_url" required type="url" /></label>
        <label className="span-2">Affiliate link<input name="affiliate_url" required type="url" /></label>
        <label>Price (PHP)<input name="price_php" required inputMode="decimal" placeholder="349.00" /></label>
        <label>Commission rate (%)<input name="commission_rate_pct" required inputMode="decimal" placeholder="8.5" /></label>
        <label>Rating (0–5)<input name="rating" inputMode="decimal" placeholder="4.8" /></label>
        <label>Reviews<input name="review_count" inputMode="numeric" /></label>
        <label>Sold<input name="sold_count" inputMode="numeric" /></label>
        <label>Seller name<input name="seller_name" maxLength={240} /></label>
        <label className="checkbox span-2"><input name="in_stock" type="checkbox" defaultChecked /> In stock now</label>
        <label className="span-2">
          Verified facts, one per line
          <textarea name="verified_facts" rows={4} placeholder={"USB-C charging\n3 speed settings"} />
          <small>Copy these from the listing. Generated copy may only state these facts.</small>
        </label>
        <label className="span-2">Image URL (the listing&apos;s own photo)<input name="image_url" type="url" /></label>
        <label className="span-2">Image usage note<input name="image_usage_note" placeholder="Seller photo, allowed for affiliate posts" /></label>
        <label className="span-2">Shipping note<input name="shipping_note" /></label>
        <label className="span-2">Notes<textarea name="notes" rows={2} /></label>
      </div>
      <button className="button" disabled={pending} type="submit">{pending ? "Saving…" : "Add listing"}</button>
      <FormMessage state={state} />
    </form>
  );
}

/** Log a search that found nothing usable. These feed future marketplace-fit priors. */
export function SearchFailureForm({ opportunityId, defaultQuery }: { opportunityId: string; defaultQuery: string }) {
  const [state, action, pending] = useActionState(logSearchFailure.bind(null, opportunityId), null);

  return (
    <form action={action} className="stack-form">
      <div className="form-grid">
        <MarketplaceSelect />
        <label>
          Reason
          <select name="reason" required defaultValue="no_results">
            <option value="no_results">No results</option>
            <option value="not_affiliate_eligible">Not affiliate-eligible</option>
            <option value="low_commission">Commission too low</option>
            <option value="poor_quality">Poor quality or reviews</option>
            <option value="out_of_stock">Out of stock</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label className="span-2">Search used<input name="query" required defaultValue={defaultQuery} minLength={2} /></label>
        <label className="span-2">Note<input name="note" /></label>
      </div>
      <button className="button secondary" disabled={pending} type="submit">{pending ? "Saving…" : "Log failed search"}</button>
      <FormMessage state={state} />
    </form>
  );
}
