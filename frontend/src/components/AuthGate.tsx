"use client";

import { useEffect, useState } from "react";
import { BoardApp } from "./BoardApp";
import { LoginForm } from "./LoginForm";

type AuthStatus = "checking" | "authenticated" | "anonymous";

export function AuthGate() {
  const [status, setStatus] = useState<AuthStatus>("checking");

  useEffect(() => {
    fetch("/api/me", { credentials: "include" })
      .then((response) => setStatus(response.ok ? "authenticated" : "anonymous"))
      .catch(() => setStatus("anonymous"));
  }, []);

  if (status === "checking") return null;
  if (status === "anonymous") return <LoginForm onSuccess={() => setStatus("authenticated")} />;
  return <BoardApp onLogout={() => setStatus("anonymous")} />;
}
