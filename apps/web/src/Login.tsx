import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api, post, saveSession, schoolAuthEnabled, type SessionUser } from "./api";

type Props = {
  onLogin: (user: SessionUser) => void;
};

type Health = {
  google_login?: boolean;
  google_allowed_domain?: string | null;
  school_auth?: boolean;
};

function googleLoginConfigured(): boolean {
  return String(import.meta.env.VITE_FEATURE_GOOGLE_LOGIN || "false").toLowerCase() === "true";
}

function supabaseUrl(): string {
  return String(import.meta.env.VITE_SUPABASE_URL || "").replace(/\/$/, "");
}

function supabaseAnonKey(): string {
  return String(import.meta.env.VITE_SUPABASE_ANON_KEY || "");
}

function parseHashToken(): string | null {
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) return null;
  const params = new URLSearchParams(hash);
  return params.get("access_token");
}

export default function Login({ onLogin }: Props) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const showGoogle =
    googleLoginConfigured() && Boolean(health?.google_login) && Boolean(supabaseUrl());
  const showLocal = schoolAuthEnabled();

  useEffect(() => {
    void api<Health>("/health")
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    const token = parseHashToken();
    if (!token || !showGoogle) return;
    let cancelled = false;
    (async () => {
      setBusy(true);
      setError("");
      try {
        const data = await api<{ token: string; user: SessionUser }>(
          "/auth/google",
          post({ access_token: token }),
        );
        if (cancelled) return;
        saveSession({ token: data.token, user: data.user });
        window.history.replaceState(null, "", window.location.pathname + window.location.search);
        onLogin(data.user);
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
          window.history.replaceState(null, "", window.location.pathname + window.location.search);
        }
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [onLogin, showGoogle]);

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

  function startGoogle() {
    const base = supabaseUrl();
    const anon = supabaseAnonKey();
    if (!base || !anon) {
      setError("Falta VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY en el entorno web.");
      return;
    }
    const redirectTo = `${window.location.origin}${window.location.pathname}`;
    const url = new URL(`${base}/auth/v1/authorize`);
    url.searchParams.set("provider", "google");
    url.searchParams.set("redirect_to", redirectTo);
    url.searchParams.set("apikey", anon);
    window.location.href = url.toString();
  }

  return (
    <main className="shell narrow">
      <section className="panel">
        <div className="activity-heading">
          <h1>Iniciar sesión</h1>
        </div>
        <p className="field-hint">
          {showGoogle
            ? `Cuenta institucional @${health?.google_allowed_domain || "montessorisucre.edu.bo"} (Google Workspace).`
            : "Usa tu cuenta institucional de MONTI (administrador, profesor o alumno)."}
        </p>
        {showGoogle ? (
          <div className="stack" style={{ marginBottom: "1rem" }}>
            <button type="button" disabled={busy} onClick={startGoogle}>
              {busy ? "Conectando…" : "Continuar con Google"}
            </button>
            <p className="field-hint">
              MONTI no guarda contraseñas del colegio. Debes estar en el roster
              del piloto.
            </p>
          </div>
        ) : null}
        {showLocal ? (
          <form className="stack" onSubmit={submit}>
            {showGoogle ? <p className="field-hint">O acceso local de desarrollo:</p> : null}
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
        ) : error ? (
          <p className="notice error" role="alert">
            {error}
          </p>
        ) : null}
        {!showGoogle && !showLocal ? (
          <p className="notice error" role="alert">
            No hay método de login habilitado. Activa school auth o Google login.
          </p>
        ) : null}
      </section>
    </main>
  );
}
