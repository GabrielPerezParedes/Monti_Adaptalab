import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  GoogleAuthProvider,
  getRedirectResult,
  signInWithPopup,
  type UserCredential,
} from "firebase/auth";
import { api, post, saveSession, schoolAuthEnabled, type SessionUser } from "./api";
import { firebaseAuth, firebaseConfigured } from "./firebase";

type Props = {
  onLogin: (user: SessionUser) => void;
};

type Health = {
  google_login?: boolean;
  google_allowed_domain?: string | null;
  school_auth?: boolean;
};

/** Una sola lectura: StrictMode llama useEffect 2 veces y consumiría el redirect. */
let redirectResultPromise: Promise<UserCredential | null> | null = null;

function readRedirectResult(): Promise<UserCredential | null> {
  if (!firebaseAuth) return Promise.resolve(null);
  if (!redirectResultPromise) {
    redirectResultPromise = getRedirectResult(firebaseAuth).catch((err) => {
      redirectResultPromise = null;
      throw err;
    });
  }
  return redirectResultPromise;
}

function googleLoginConfigured(): boolean {
  return String(import.meta.env.VITE_FEATURE_GOOGLE_LOGIN || "false").toLowerCase() === "true";
}

function googleProvider(allowedDomain: string) {
  const provider = new GoogleAuthProvider();
  provider.addScope("email");
  provider.addScope("profile");
  provider.setCustomParameters({ hd: allowedDomain, prompt: "select_account" });
  return provider;
}

async function exchangeGoogleSession(
  credential: UserCredential,
  onLogin: (user: SessionUser) => void,
) {
  const idToken = await credential.user.getIdToken();
  const data = await api<{ token: string; user: SessionUser }>(
    "/auth/google",
    post({ access_token: idToken }),
  );
  saveSession({ token: data.token, user: data.user });
  onLogin(data.user);
}

export default function Login({ onLogin }: Props) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const showGoogle =
    googleLoginConfigured() && Boolean(health?.google_login) && firebaseConfigured();
  const showLocal = schoolAuthEnabled();
  const allowedDomain = health?.google_allowed_domain || "montessorisucre.edu.bo";

  useEffect(() => {
    void api<Health>("/health")
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    if (!firebaseAuth || !showGoogle) return;
    let cancelled = false;
    (async () => {
      setBusy(true);
      try {
        const result = await readRedirectResult();
        if (cancelled || !result) return;
        await exchangeGoogleSession(result, onLogin);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof TypeError
              ? "No hay conexión con el servidor. Revisa la red e inténtalo de nuevo."
              : (err as Error).message,
          );
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

  async function startGoogle() {
    if (!firebaseAuth) {
      setError("Falta configuración Firebase (VITE_FIREBASE_*) en el entorno web.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await signInWithPopup(firebaseAuth, googleProvider(allowedDomain));
      await exchangeGoogleSession(result, onLogin);
    } catch (err) {
      const code =
        typeof err === "object" && err && "code" in err ? String((err as { code: string }).code) : "";
      if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") {
        setError("");
      } else {
        setError(
          err instanceof TypeError
            ? "No hay conexión con el servidor. Revisa la red e inténtalo de nuevo."
            : (err as Error).message,
        );
      }
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
          {showGoogle
            ? `Cuenta institucional @${allowedDomain} (Google Workspace).`
            : "Usa tu cuenta institucional de MONTI (administrador, profesor o alumno)."}
        </p>
        {showGoogle ? (
          <div className="stack" style={{ marginBottom: "1rem" }}>
            <button type="button" disabled={busy} onClick={() => void startGoogle()}>
              {busy ? "Conectando…" : "Continuar con Google"}
            </button>
            <p className="field-hint">
              MONTI no guarda contraseñas del colegio. Debes estar en el roster
              del piloto. Usa http://localhost:5173 (no 127.0.0.1).
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
