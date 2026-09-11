import { useState } from "react";
import type { FormEvent } from "react";
import { api, post, saveSession, type SessionUser } from "./api";

type Props = {
  onLogin: (user: SessionUser) => void;
};

export default function Login({ onLogin }: Props) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api<{ token: string; user: SessionUser }>(
        "/auth/login",
        post({ login, password }),
      );
      saveSession({ token: data.token, user: data.user });
      onLogin(data.user);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "No hay conexión con el servidor. Revisa la red e inténtalo de nuevo."
          : (err as Error).message,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell narrow">
      <section className="panel">
        <div className="activity-heading">
          <h1>Iniciar sesión</h1>
        </div>
        <p className="field-hint">
          Usa tu cuenta institucional de MONTI (administrador, profesor o
          alumno).
        </p>
        <form className="stack" onSubmit={submit}>
          <label>
            Identificador
            <input
              autoComplete="username"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              required
            />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error ? (
            <p className="notice error" role="alert">
              {error}
            </p>
          ) : null}
          <button disabled={busy}>{busy ? "Entrando…" : "Entrar"}</button>
        </form>
      </section>
    </main>
  );
}
