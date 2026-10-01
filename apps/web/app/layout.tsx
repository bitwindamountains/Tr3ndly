import "@fontsource-variable/manrope";
import "@fontsource-variable/space-grotesk";
import "./styles.css";

import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Tr3ndly — Opportunity intelligence",
  description: "Evidence-backed affiliate opportunities for Philippine creators.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

