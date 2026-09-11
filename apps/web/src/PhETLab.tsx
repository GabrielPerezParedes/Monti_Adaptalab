import { useEffect, useRef, useState } from "react";
import type { Lab, Launch, SimEvent } from "./types";

const kinds = new Set([
  "control",
  "launch",
  "landed",
  "reset",
  "erase",
  "measurement",
  "pause",
  "invalidated",
]);
export default function PhETLab({
  lab,
  onEvent,
  onState,
}: {
  lab: Lab;
  onEvent: (event: SimEvent) => void;
  onState: (state: Launch) => void;
}) {
  const frame = useRef<HTMLIFrameElement>(null);
  const callbacks = useRef({ onEvent, onState });
  callbacks.current = { onEvent, onState };
  const [channel] = useState(() => crypto.randomUUID());
  const [ready, setReady] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const source = `/phet/projectile-motion.html?montiChannel=${channel}&screens=1&showHomeScreen=false`;

  useEffect(() => {
    let alive = true;
    fetch("/phet/projectile-motion.html")
      .then(async (r) => {
        const text = await r.text();
        if (alive) setAvailable(r.ok && text.includes("monti:ready"));
      })
      .catch(() => {
        if (alive) setAvailable(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    const listener = (event: MessageEvent) => {
      if (
        event.origin !== location.origin ||
        event.source !== frame.current?.contentWindow
      )
        return;
      const data = event.data;
      if (
        !data ||
        typeof data !== "object" ||
        data.channel !== channel ||
        data.version !== 1
      )
        return;
      if (data.type === "monti:ready") {
        frame.current?.contentWindow?.postMessage(
          { type: "monti:configure", version: 1, channel, lab },
          location.origin,
        );
      } else if (data.type === "monti:configured") {
        setReady(true);
        setError("");
      } else if (
        data.type === "monti:state" &&
        data.state &&
        typeof data.state === "object"
      ) {
        callbacks.current.onState(data.state as Launch);
      } else if (
        data.type === "monti:event" &&
        data.event &&
        kinds.has(data.event.kind) &&
        typeof data.event.id === "string"
      ) {
        callbacks.current.onEvent(data.event as SimEvent);
      } else if (data.type === "monti:error")
        setError(String(data.message).slice(0, 250));
    };
    window.addEventListener("message", listener);
    return () => window.removeEventListener("message", listener);
  }, [channel, lab]);

  useEffect(() => {
    if (!available || ready) return;
    const timer = window.setTimeout(
      () =>
        setError(
          "La conexión con el laboratorio está tardando. Recarga la página para reintentar.",
        ),
      25000,
    );
    return () => clearTimeout(timer);
  }, [available, ready]);

  if (available === false)
    return (
      <div className="sim-empty">
        <strong>Falta preparar el simulador en este equipo</strong>
        <p>
          Ejecuta la preparación de PhET indicada en el README y vuelve a abrir
          esta actividad.
        </p>
      </div>
    );
  return (
    <div className="sim-stage">
      {!ready && (
        <p className="sim-loading" role="status">
          {error || "Cargando el laboratorio…"}
        </p>
      )}
      {ready && error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {available && (
        <iframe
          ref={frame}
          src={source}
          title="PhET: laboratorio de movimiento parabólico"
          className="phet-frame"
        />
      )}
      {ready && <span className="connection">Laboratorio conectado</span>}
    </div>
  );
}
