"use client";

import { useState, type FormEvent } from "react";

type LoginFormProps = {
  onSuccess: () => void;
};

export function LoginForm({ onSuccess }: LoginFormProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) {
        setError("Usuario o contraseña incorrectos.");
        return;
      }
      onSuccess();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-xl bg-white p-6 shadow-sm"
      >
        <h1 className="text-xl font-bold text-navy">Iniciar sesión</h1>
        <div className="flex flex-col gap-1">
          <label htmlFor="username" className="text-sm text-muted-gray">
            Usuario
          </label>
          <input
            id="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm text-navy outline-none focus:border-primary-blue focus:ring-1 focus:ring-primary-blue"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="password" className="text-sm text-muted-gray">
            Contraseña
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm text-navy outline-none focus:border-primary-blue focus:ring-1 focus:ring-primary-blue"
          />
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-secondary-purple px-3 py-2 text-sm font-medium text-white hover:bg-secondary-purple-dark disabled:opacity-60"
        >
          Entrar
        </button>
      </form>
    </div>
  );
}
