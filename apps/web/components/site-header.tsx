import { LogOut } from "lucide-react";
import Link from "next/link";

import { logout } from "@/app/actions";
import { authConfig } from "@/lib/session";
import { Brand } from "./brand";

const links = [
  { href: "/", label: "Today", key: "today" },
  { href: "/operations", label: "Operations", key: "operations" },
] as const;

export function SiteHeader({ active }: { active?: (typeof links)[number]["key"] }) {
  return (
    <header className="topbar">
      <Link className="brand-link" href="/"><Brand /></Link>
      <nav aria-label="Primary navigation">
        {links.map((link) => (
          <Link
            aria-current={active === link.key ? "page" : undefined}
            className={active === link.key ? "active" : undefined}
            href={link.href}
            key={link.key}
          >
            {link.label}
          </Link>
        ))}
      </nav>
      <div className="header-actions">
        {authConfig() && (
          <form action={logout}>
            <button className="icon-button" aria-label="Sign out" title="Sign out" type="submit">
              <LogOut size={17} />
            </button>
          </form>
        )}
      </div>
    </header>
  );
}
