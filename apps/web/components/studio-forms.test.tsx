import { render, screen } from "@testing-library/react";

import type { CreativeVariant } from "@/lib/types";
import { VariantCard } from "./studio-forms";

vi.mock("@/app/actions", () => ({
  createBrief: vi.fn(),
  exportCopy: vi.fn(),
  generateCopy: vi.fn(),
  reviewCopy: vi.fn(),
}));

const variant: CreativeVariant = {
  id: "v1",
  brief_id: "b1",
  parent_id: null,
  hook_type: "benefit",
  hook: "The best fan, only ₱349",
  caption: "From the listing: USB-C charging.",
  cta: "Tap the link.",
  hashtags: ["#Fan"],
  generator: "template",
  prompt_version: "copy-template-v1",
  policy_issues: [],
  status: "needs_review",
  tracking_code: null,
  exported_at: null,
  created_at: "2026-10-08T00:00:00Z",
};

describe("VariantCard", () => {
  it("blocks approval while a variant has blocking policy issues", () => {
    render(
      <VariantCard
        variant={{
          ...variant,
          policy_issues: [
            { code: "price", field: "hook", match: "₱349", message: "Prices change.", blocking: true },
          ],
        }}
      />,
    );

    expect(screen.getByRole("button", { name: "Approve" })).toBeDisabled();
    expect(screen.getByText(/“₱349” in hook/)).toBeInTheDocument();
  });

  it("offers export only for approved copy and a link once exported", () => {
    const { rerender } = render(<VariantCard variant={{ ...variant, status: "approved" }} />);
    expect(screen.getByRole("button", { name: "Export" })).toBeEnabled();

    rerender(<VariantCard variant={{ ...variant, status: "exported", tracking_code: "t3abcd1234" }} />);
    expect(screen.queryByRole("button", { name: "Export" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /t3abcd1234/ })).toHaveAttribute("href", "/exports/v1");
  });
});
