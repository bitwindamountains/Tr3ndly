import { redirect } from "next/navigation";

import { Brand } from "@/components/brand";
import { LoginForm } from "@/components/login-form";
import { isOperator } from "@/lib/auth";
import { authConfig, safeNextPath } from "@/lib/session";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const next = safeNextPath((await searchParams).next);
  if (!authConfig() || (await isOperator())) redirect(next);

  return (
    <main className="shell login-shell">
      <Brand />
      <h1>Sign in to the opportunity desk</h1>
      <LoginForm next={next} />
    </main>
  );
}
