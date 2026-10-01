import { render, screen } from "@testing-library/react";

import { Brand } from "./brand";

describe("Brand", () => {
  it("renders the product name", () => {
    render(<Brand />);
    expect(screen.getByLabelText("Tr3ndly")).toHaveTextContent("tr3ndly");
  });
});

