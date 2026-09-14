import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  api,
  loadSession,
  post,
  saveSession,
  schoolAuthEnabled,
  type SessionUser,
} from "./api";
import PhETLab from "./PhETLab";
import MontiCompanion from "./MontiCompanion";
import Login from "./Login";
import Admin from "./Admin";
import type {
  Attempt,
  Difficulty,
  Lab,
  Launch,
  Report,
  SimEvent,
} from "./types";

const levels: Record<Difficulty, string> = {
  basic: "Básica",
  medium: "Media",
  advanced: "Avanzada",
};
const names = {
  procedure: "Procedimiento",
  comprehension: "Comprensión",
  physical: "Resultado físico",
  efficiency: "Eficiencia",
};
const max = { procedure: 18, comprehension: 14, physical: 9, efficiency: 4 };
const controls: Record<string, string> = {
  speed_m_s: "Rapidez inicial (m/s)",
  angle_deg: "Ángulo (°)",
  height_m: "Altura (m)",
  gravity_m_s2: "Gravedad (m/s²)",
  air_resistance: "Resistencia del aire",
  totalVelocityVectorOnProperty: "Vector de velocidad",
  componentsVelocityVectorsOnProperty: "Componentes de velocidad",
  totalAccelerationVectorOnProperty: "Vector de aceleración",
  componentsAccelerationVectorsOnProperty: "Componentes de aceleración",
  zoom: "Ampliación",
  timeSpeed: "Velocidad de reproducción",
  measuringTape: "Cinta métrica",
  measuringTapeLength_m: "Longitud medida (m)",
  dataProbe: "Sonda de datos",
};

const format = (v: number | null | undefined, digits = 2) =>
  v == null
    ? "Pendiente"
    : v.toLocaleString("es-BO", { maximumFractionDigits: digits });

function ErrorNotice({ text }: { text: string }) {
  return text ? (
    <p className="notice error" role="alert">
      {text}
    </p>
  ) : null;
}

function Scores({ report }: { report: Report }) {
  return (
    <div className="score-grid">
      {(Object.keys(names) as (keyof typeof names)[]).map((key) => (
        <div key={key}>
          <span>{names[key]}</span>
          <strong>
            {format(report.scores[key])}
            <small> / {max[key]}</small>
          </strong>
        </div>
      ))}
    </div>
  );
}

function Teacher() {
  const [labs, setLabs] = useState<Lab[]>([]),
    [current, setCurrent] = useState<Lab | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("basic"),
    [course, setCourse] = useState("4.º de secundaria");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [copied, setCopied] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const refresh = useCallback(async () => {
    try {
      const rows = await api<Lab[]>("/teacher/labs", {}, undefined, true);
      setLabs(rows);
      setCurrent((value) => value || rows[0] || null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  useEffect(() => {
    if (!current) return;
    let alive = true;
    const load = async () => {
      try {
        const value = await api<Report[]>(
          `/teacher/labs/${current.id}/results`,
          {},
          undefined,
          true,
        );
        if (alive) setReports(value);
      } catch (e) {
        if (alive) setError((e as Error).message);
      }
    };
    void load();
    const timer = setInterval(load, 4000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [current?.id]);

  async function create(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const seed = crypto.getRandomValues(new Uint32Array(1))[0] % 2147483647;
      const lab = await api<Lab>(
        "/teacher/labs",
        post({ course, difficulty, seed }),
        undefined,
        true,
      );
      setCurrent(lab);
      setReports([]);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function publish() {
    if (!current) return;
    setBusy(true);
    setError("");
    try {
      await api(`/teacher/labs/${current.id}/publish`, post(), undefined, true);
      setCurrent({ ...current, published: true });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function downloadClass() {
    if (!current) return;
    try {
      const r = await fetch(`/api/teacher/labs/${current.id}/report.txt`, {
        headers: {
          "X-Teacher-Key":
            import.meta.env.VITE_DEV_TEACHER_KEY || "monti-local-teacher",
        },
      });
      if (!r.ok) throw new Error("No se pudo descargar el resumen del curso.");
      const url = URL.createObjectURL(await r.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = `MONTI-curso-${current.id}.txt`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => setCopied(false), [current?.id]);
  const link = current ? `${location.origin}/student?lab=${current.id}` : "";
  return (
    <main className="workspace teacher-workspace">
      <div className="page-heading">
        <div>
          <span className="eyebrow">ESPACIO DOCENTE</span>
          <h1>Prepara el próximo experimento.</h1>
          <p>Movimiento parabólico · 4.º de secundaria</p>
        </div>
        <span className="subject-tag">Física / 2D</span>
      </div>
      <ErrorNotice text={error} />
      <div className="teacher-layout">
        <section className="panel configuration">
          <div className="section-label">
            <span>01</span>
            <h2>Configurar actividad</h2>
          </div>
          <form onSubmit={create}>
            <label>
              Curso
              <input
                value={course}
                maxLength={60}
                required
                onChange={(e) => setCourse(e.target.value)}
              />
            </label>
            <label>
              Tema
              <input value="Movimiento parabólico" readOnly />
            </label>
            <fieldset>
              <legend>Dificultad</legend>
              <div className="level-options">
                {(Object.keys(levels) as Difficulty[]).map((level) => (
                  <label
                    key={level}
                    className={difficulty === level ? "selected" : ""}
                  >
                    <input
                      type="radio"
                      name="difficulty"
                      value={level}
                      checked={difficulty === level}
                      onChange={() => setDifficulty(level)}
                    />
                    {levels[level]}
                  </label>
                ))}
              </div>
            </fieldset>
            <p className="field-hint">
              {difficulty === "basic"
                ? "Explora el ángulo con la rapidez fijada."
                : difficulty === "medium"
                  ? "Ajusta el ángulo y la rapidez inicial."
                  : "Trabaja con una altura inicial y justifica tu predicción."}
            </p>
            <button className="primary" disabled={busy}>
              {busy ? "Preparando…" : "Preparar laboratorio"}
            </button>
          </form>
          <div className="rubric-mini">
            <h3>Evaluación / 45 puntos</h3>
            <p>
              Procedimiento <b>18</b> · Comprensión <b>14</b>
              <br />
              Resultado <b>9</b> · Eficiencia <b>4</b>
            </p>
          </div>
        </section>
        <section className="panel activity-preview">
          <div className="section-label">
            <span>02</span>
            <h2>Revisar y publicar</h2>
          </div>
          {!current ? (
            <div className="empty">
              <span className="empty-symbol">↗</span>
              <h3>Tu primera actividad empieza aquí.</h3>
              <p>
                Prepara un laboratorio para revisar la consigna y abrirlo al
                curso.
              </p>
            </div>
          ) : (
            <>
              <label className="activity-picker">
                Actividad
                <select
                  value={current.id}
                  onChange={(e) => {
                    setCurrent(
                      labs.find((l) => l.id === e.target.value) || null,
                    );
                    setReports([]);
                  }}
                >
                  {labs.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.course} · {levels[l.difficulty]} · {l.id}
                    </option>
                  ))}
                </select>
              </label>
              <div className="activity-heading">
                <h3>{current.title}</h3>
                <span
                  className={`badge ${current.published ? "published" : ""}`}
                >
                  {current.published ? "Publicada" : "En preparación"}
                </span>
              </div>
              <p className="instruction">{current.instruction}</p>
              <div className="facts">
                <div>
                  <span>Objetivo</span>
                  <strong>
                    {format(current.target_m)} <small>m</small>
                  </strong>
                </div>
                <div>
                  <span>Tolerancia</span>
                  <strong>
                    ± {format(current.tolerance_m)} <small>m</small>
                  </strong>
                </div>
                <div>
                  <span>Gravedad</span>
                  <strong>
                    10 <small>m/s²</small>
                  </strong>
                </div>
              </div>
              <p className="field-hint">
                Altura inicial: {current.initial.height_m} m. Rapidez inicial:{" "}
                {current.initial.speed_m_s} m/s. Sin resistencia del aire.
              </p>
              <div className="activity-code-share">
                <label>Código de la actividad<input readOnly value={current.id} aria-label="Código de la actividad" onFocus={e => e.target.select()} /></label>
                <button type="button" className="secondary" onClick={async () => { try { await navigator.clipboard.writeText(current.id); } catch { setError('Selecciona y copia el código visible.'); } }}>Copiar código</button>
              </div>
              <div className="share-row">
                <input
                  aria-label="Enlace del estudiante"
                  readOnly
                  value={link}
                />
                <button
                  className="secondary"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(link);
                      setCopied(true);
                    } catch {
                      setError("Selecciona y copia el enlace de la actividad.");
                    }
                  }}
                >
                  {copied ? "Copiado" : "Copiar enlace"}
                </button>
              </div>
              <p className="field-hint">
                Puedes compartir el enlace antes de publicar: el estudiante verá
                la sala de espera.
              </p>
              <button
                className="primary"
                disabled={busy || current.published}
                onClick={publish}
              >
                {current.published
                  ? "Disponible para el curso"
                  : "Publicar para el curso"}
              </button>
            </>
          )}
        </section>
      </div>
      <section className="panel results">
        <div className="section-label">
          <span>03</span>
          <h2>Trabajo del curso</h2>
        </div>
        {reports.length > 0 && (
          <button className="secondary" onClick={downloadClass}>
            Descargar resúmenes del curso
          </button>
        )}
        {reports.length === 0 ? (
          <p className="muted">
            Los resultados aparecerán cuando ingresen los estudiantes.
          </p>
        ) : (
          <div className="results-list">
            {reports.map((r) => (
              <ResultRow
                key={r.id}
                report={r}
                onReview={(r) =>
                  setReports((rows) =>
                    rows.map((old) => (old.id === r.id ? r : old)),
                  )
                }
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function ResultRow({
  report,
  onReview,
}: {
  report: Report;
  onReview: (r: Report) => void;
}) {
  const [open, setOpen] = useState(false),
    [procedure, setProcedure] = useState(report.scores.procedure || 0),
    [understanding, setUnderstanding] = useState(
      report.scores.comprehension || 0,
    ),
    [reason, setReason] = useState(""),
    [error, setError] = useState("");
  async function review(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      onReview(
        await api<Report>(
          `/teacher/attempts/${report.id}/review`,
          post({ procedure, comprehension: understanding, reason }),
          undefined,
          true,
        ),
      );
      setOpen(false);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <article className="result-row">
      <button
        className="result-toggle"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <strong>{report.alias}</strong>
        <span>{report.run_count} lanzamientos</span>
        <span>
          {report.passed == null
            ? "En actividad"
            : report.passed
              ? "Objetivo alcanzado"
              : "Resultado por revisar"}
        </span>
        <b>
          {report.total == null ? "Pendiente" : `${format(report.total)} / 45`}
        </b>
      </button>
      {open && (
        <div className="result-detail">
          <p>{report.summary}</p>
          <Scores report={report} />
          <details className="evidence">
            <summary>
              Ver acciones registradas ({report.evidence.length})
            </summary>
            <ol>
              {report.evidence.map((event) => (
                <li key={event.id}>
                  <b>
                    {
                      {
                        control: "Ajuste",
                        launch: "Lanzamiento",
                        landed: "Llegada al suelo",
                        reset: "Reinicio",
                        erase: "Borrado",
                        measurement: "Medición",
                        pause: "Pausa",
                        invalidated: "Invalidación",
                      }[event.kind]
                    }
                  </b>
                  {event.control &&
                    ` · ${controls[event.control] || "Control"}: ${typeof event.value === "boolean" ? (event.value ? "Activado" : "Desactivado") : event.value}`}
                  {event.state &&
                    ` · ${event.state.angle_deg}° · ${event.state.speed_m_s} m/s · ${event.state.height_m} m`}
                  {event.observed_range_m != null &&
                    ` · ${format(event.observed_range_m)} m`}
                </li>
              ))}
            </ol>
          </details>
          {report.reviews.map((review, i) => (
            <p className="field-hint" key={i}>
              Revisión {i + 1}: {review.reason}
            </p>
          ))}
          {report.explanations.map((entry, i) => (
            <blockquote key={i}>{entry.text}</blockquote>
          ))}
          {report.result && (
            <form onSubmit={review} className="review-form">
              <label>
                Procedimiento /18
                <input
                  type="number"
                  min={0}
                  max={18}
                  step={0.5}
                  value={procedure}
                  onChange={(e) => setProcedure(Number(e.target.value))}
                  required
                />
              </label>
              <label>
                Comprensión /14
                <input
                  type="number"
                  min={0}
                  max={14}
                  step={0.5}
                  value={understanding}
                  onChange={(e) => setUnderstanding(Number(e.target.value))}
                  required
                />
              </label>
              <label className="wide">
                Fundamento de la valoración
                <textarea
                  minLength={5}
                  maxLength={1000}
                  required
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
              <button className="secondary">Guardar revisión</button>
            </form>
          )}
          <ErrorNotice text={error} />
        </div>
      )}
    </article>
  );
}

function Student() {
  const initialCode = (new URLSearchParams(location.search).get("lab") || "").trim().toLowerCase();
  const [code, setCode] = useState(initialCode),
    [activeCode, setActiveCode] = useState(initialCode),
    [lab, setLab] = useState<Lab | null>(null),
    [waiting, setWaiting] = useState(false);
  const [attempt, setAttempt] = useState<Attempt | null>(null),
    [alias, setAlias] = useState("Estudiante de prueba"),
    [enrollmentId, setEnrollmentId] = useState(""),
    [enrollments, setEnrollments] = useState<
      { id: string; grade_id: string; subject_id: string; is_active: boolean }[]
    >([]);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [state, setState] = useState<Launch | null>(null);
  const [report, setReport] = useState<Report | null>(null),
    [prompt, setPrompt] = useState(
      "¿Qué variable vas a cambiar primero y qué esperas observar?",
    ),
    [answer, setAnswer] = useState(""),
    [saved, setSaved] = useState(false);
  const [lastLanded, setLastLanded] = useState<string | null>(null),
    [pendingCount, setPendingCount] = useState(0);
  const queue = useRef<SimEvent[]>([]),
    flushing = useRef<Promise<void> | null>(null);

  useEffect(() => {
    if (!activeCode) return;
    let alive = true;
    const load = async () => {
      try {
        const value = await api<{
          published: boolean;
          spec: Lab | null;
          id: string;
        }>(`/labs/${encodeURIComponent(activeCode)}`);
        if (!alive) return;
        setError("");
        setWaiting(!value.published);
        if (value.spec)
          setLab((old) =>
            old?.id === value.id
              ? old
              : { ...value.spec!, id: value.id, published: true },
          );
      } catch (e) {
        if (alive) setError((e as Error).message);
      }
    };
    void load();
    const timer = setInterval(load, 3000);
    try {
      const old = localStorage.getItem(`monti-attempt-${activeCode}`);
      if (old) setAttempt(JSON.parse(old));
    } catch {
      /* Invalid local preference; a new join remains available. */
    }
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [activeCode]);

  useEffect(() => {
    if (!attempt) return;
    try {
      queue.current = JSON.parse(
        localStorage.getItem(`monti-events-${attempt.id}`) || "[]",
      );
      setPendingCount(queue.current.length);
    } catch {
      queue.current = [];
    }
  }, [attempt?.id]);

  const refreshReport = useCallback(async () => {
    if (!attempt) return;
    const [r, p] = await Promise.all([
      api<Report>(`/attempts/${attempt.id}/report`, {}, attempt),
      api<{ text: string }>(`/attempts/${attempt.id}/prompt`, {}, attempt),
    ]);
    setReport(r);
    setPrompt(p.text);
  }, [attempt]);

  const flush = useCallback(async () => {
    if (!attempt) return;
    if (flushing.current) return flushing.current;
    const work = async () => {
      while (queue.current.length) {
        const events = queue.current.slice(0, 100);
        const response = await api<{ accepted: string[] }>(
          `/attempts/${attempt.id}/events`,
          post({ events }),
          attempt,
        );
        const accepted = new Set(response.accepted);
        queue.current = queue.current.filter((e) => !accepted.has(e.id));
        localStorage.setItem(
          `monti-events-${attempt.id}`,
          JSON.stringify(queue.current),
        );
        setPendingCount(queue.current.length);
      }
    };
    const promise = work();
    flushing.current = promise;
    try {
      await promise;
    } finally {
      flushing.current = null;
    }
  }, [attempt]);

  useEffect(() => {
    if (!attempt) return;
    const tick = async () => {
      try {
        await flush();
        await refreshReport();
      } catch (e) {
        setError((e as Error).message);
      }
    };
    void tick();
    const timer = setInterval(tick, 2500);
    return () => clearInterval(timer);
  }, [attempt, flush, refreshReport]);

  function event(event: SimEvent) {
    if (!attempt) return;
    queue.current.push(event);
    localStorage.setItem(
      `monti-events-${attempt.id}`,
      JSON.stringify(queue.current),
    );
    setPendingCount(queue.current.length);
    if (event.kind === "landed") setLastLanded(event.run_id || null);
    if (["reset", "erase", "launch"].includes(event.kind)) setLastLanded(null);
  }
  useEffect(() => {
    if (!schoolAuthEnabled()) return;
    void api<{ id: string; grade_id: string; subject_id: string; is_active: boolean }[]>(
      "/student/enrollments",
    )
      .then((rows) => {
        setEnrollments(rows);
        if (rows[0]) setEnrollmentId(rows[0].id);
      })
      .catch(() => undefined);
  }, []);

  async function join(e: FormEvent) {
    e.preventDefault();
    if (!lab) return;
    setBusy(true);
    setError("");
    try {
      const body = schoolAuthEnabled()
        ? { enrollment_id: enrollmentId }
        : { alias };
      const a = await api<Attempt>(`/labs/${lab.id}/join`, post(body));
      localStorage.setItem(`monti-attempt-${lab.id}`, JSON.stringify(a));
      setAttempt(a);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function evaluate() {
    if (!attempt) return;
    setBusy(true);
    setError("");
    try {
      await flush();
      await api(`/attempts/${attempt.id}/evaluate`, post(), attempt);
      setLastLanded(null);
      await refreshReport();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submit() {
    if (!attempt || !lastLanded) return;
    setBusy(true);
    setError("");
    try {
      await flush();
      setReport(
        await api<Report>(
          `/attempts/${attempt.id}/submit`,
          post({ run_id: lastLanded }),
          attempt,
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function explain(e: FormEvent) {
    e.preventDefault();
    if (!attempt) return;
    setBusy(true);
    setError("");
    try {
      await api(
        `/attempts/${attempt.id}/explanations`,
        post({ text: answer }),
        attempt,
      );
      setAnswer("");
      setSaved(true);
      await refreshReport();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function download() {
    if (!attempt) return;
    try {
      const r = await fetch(`/api/attempts/${attempt.id}/report.txt`, {
        headers: { "X-Attempt-Token": attempt.token },
      });
      if (!r.ok) throw new Error("No se pudo descargar el resumen.");
      const url = URL.createObjectURL(await r.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = `MONTI-${activeCode}.txt`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function changeActivity() {
    setActiveCode(""); setCode(""); setLab(null); setAttempt(null); setWaiting(false); setError("");
    setReport(null); setLastLanded(null); setState(null); setAnswer(""); setSaved(false);
    const url = new URL(location.href); url.searchParams.delete('lab'); history.replaceState(null, '', url);
  }
  if (!attempt || !lab) return <main className="join-workspace"><section className="panel join-panel">
    <span className="eyebrow">ESPACIO ESTUDIANTE</span><h1>Tu laboratorio de Física.</h1>
    {!activeCode ? <>
      <p>Abre el enlace que te compartió tu profesora. Si tienes un código, introdúcelo aquí.</p>
      <form onSubmit={e => { e.preventDefault(); const next = code.trim().toLowerCase(); setError(''); setActiveCode(next); const url = new URL(location.href); url.searchParams.set('lab', next); history.replaceState(null, '', url); }}>
        <label>Código que te dio tu profesora<input value={code} onChange={e => setCode(e.target.value)} required maxLength={10} pattern="[a-fA-F0-9]{10}" autoCapitalize="none" spellCheck={false} placeholder="Ej.: 9d63c20d7c" /></label>
        <button className="primary">Abrir actividad</button>
      </form>
    </> : <>
      <div className="selected-activity"><span>Actividad <strong>{activeCode}</strong></span><button className="secondary" onClick={changeActivity}>Cambiar actividad</button></div>
      {!lab && !waiting && !error && <p role="status">Buscando tu actividad…</p>}
      {waiting && <div className="waiting" role="status"><span className="pulse" /><h2>Tu profesora está preparando el laboratorio.</h2><p>Se abrirá automáticamente cuando lo publique.</p></div>}
      {lab && !attempt && <form onSubmit={join} className="join-form"><h2>{lab.topic}</h2><p>{lab.course} · Dificultad {levels[lab.difficulty].toLowerCase()}</p>
        {schoolAuthEnabled() ? (
          <label>Tu matrícula
            <select value={enrollmentId} onChange={(e) => setEnrollmentId(e.target.value)} required>
              <option value="">Selecciona</option>
              {enrollments.map((row) => (
                <option key={row.id} value={row.id}>{row.id.slice(0, 8)}…</option>
              ))}
            </select>
          </label>
        ) : (
          <label>Tu nombre o alias de prueba<input value={alias} onChange={e => setAlias(e.target.value)} required maxLength={40} autoComplete="nickname" /></label>
        )}
        <button className="primary" disabled={busy}>{busy ? 'Entrando…' : 'Entrar al laboratorio'}</button>
      </form>}
    </>}
    <ErrorNotice text={error} />
  </section></main>;
  return (
    <main className="workspace student-workspace">
      <div className="page-heading">
        <div>
          <span className="eyebrow">
            {lab.course.toUpperCase()} · {levels[lab.difficulty].toUpperCase()}
          </span>
          <h1>{lab.topic}</h1>
        </div>
        <span className="badge">
          {report?.phase === "evaluation" ? "Evaluación" : "Exploración"}
        </span>
      </div>
      <ErrorNotice text={error} />
      <section className="activity-brief">
        <div>
          <span className="eyebrow">TU DESAFÍO</span>
          <p>{lab.instruction}</p>
        </div>
        <div className="target-readout">
          <strong>{format(lab.target_m)} m</strong>
          <span>Tolerancia ±{format(lab.tolerance_m)} m</span>
        </div>
      </section>
      <div className="student-layout companion-layout">
        <section className="lab-column">
          <div className="simulation-workspace">
            <PhETLab key={`${lab.id}-${attempt.id}`} lab={lab} onEvent={event} onState={setState} />
            <MontiCompanion key={`monti-${attempt.id}`} prompt={prompt} answer={answer} busy={busy} saved={saved}
              onAnswer={value => { setAnswer(value); setSaved(false); }}
              onTranscript={text => { if (text) { setAnswer(value => `${value}${value ? ' ' : ''}${text}`.slice(0, 2000)); setSaved(false); } }}
              onSave={explain} />
          </div>
          <div className="experiment-footer">
            <div className="current-values">
              <span>
                Ángulo{" "}
                <b>{format(state?.angle_deg ?? lab.initial.angle_deg)}°</b>
              </span>
              <span>
                Rapidez{" "}
                <b>{format(state?.speed_m_s ?? lab.initial.speed_m_s)} m/s</b>
              </span>
              <span>
                Altura{" "}
                <b>{format(state?.height_m ?? lab.initial.height_m)} m</b>
              </span>
            </div>
            <small>
              {pendingCount
                ? `${pendingCount} acciones por guardar`
                : "Acciones guardadas"}
            </small>
          </div>
          <div className="action-bar">
            <p>
              {report?.phase === "evaluation"
                ? "Entrega un lanzamiento finalizado. Los fallos y reinicios se registran."
                : "Explora los controles antes de iniciar la evaluación."}
            </p>
            {report?.phase !== "evaluation" ? (
              <button
                className="primary"
                onClick={evaluate}
                disabled={busy || pendingCount > 0}
              >
                Iniciar evaluación
              </button>
            ) : (
              <button
                className="primary"
                disabled={busy || !lastLanded}
                onClick={submit}
              >
                Entregar lanzamiento
              </button>
            )}
          </div>
          {report?.result && (
            <section className="panel your-result">
              <div className="activity-heading">
                <h2>
                  {report.passed
                    ? "Objetivo alcanzado"
                    : "Revisa tu lanzamiento"}
                </h2>
                <strong>{format(report.result.range_m)} m</strong>
              </div>
              <p>{report.summary}</p>
              <Scores report={report} />
              <p className="field-hint">
                {report.total == null
                  ? "Procedimiento y comprensión pendientes de revisión docente."
                  : `Puntaje total: ${format(report.total)} / 45.`}
              </p>
              <button className="secondary" onClick={download}>
                Descargar resumen
              </button>
            </section>
          )}
        </section>

      </div>
    </main>
  );
}

export default function App() {
  const path = location.pathname;
  const student = path.startsWith("/student");
  const adminPath = path.startsWith("/admin");
  const school = schoolAuthEnabled();
  const [user, setUser] = useState<SessionUser | null>(() => loadSession()?.user ?? null);

  useEffect(() => {
    if (!school || !loadSession()?.token) return;
    void api<SessionUser & { scope?: unknown }>("/auth/me")
      .then((me) => setUser({ id: me.id, login: me.login, display_name: me.display_name, role: me.role }))
      .catch(() => {
        saveSession(null);
        setUser(null);
      });
  }, [school]);

  async function logout() {
    try {
      await api("/auth/logout", post());
    } catch {
      /* session may already be gone */
    }
    saveSession(null);
    setUser(null);
    location.href = "/login";
  }

  if (school && !user) {
    return (
      <>
        <header className="app-header">
          <a href="/login" className="brand">
            MONTI<span>Laboratorio de Física</span>
          </a>
          <span className="prototype">Acceso escolar</span>
        </header>
        <Login
          onLogin={(next) => {
            setUser(next);
            location.href =
              next.role === "admin"
                ? "/admin"
                : next.role === "student"
                  ? "/student"
                  : "/teacher";
          }}
        />
      </>
    );
  }

  if (school && user?.role === "admin" && adminPath) {
    return (
      <>
        <header className="app-header">
          <a href="/admin" className="brand">
            MONTI<span>Laboratorio de Física</span>
          </a>
          <nav aria-label="Espacios de trabajo">
            <a href="/admin" aria-current="page">
              Administración
            </a>
            <a href="/teacher">Docente</a>
          </nav>
          <span className="prototype">
            {user.display_name} · {user.role}
            <button className="secondary" type="button" onClick={() => void logout()}>
              Cerrar sesión
            </button>
          </span>
        </header>
        <Admin />
      </>
    );
  }

  return (
    <>
      <header className="app-header">
        <a href={student ? "/student" : "/teacher"} className="brand">
          MONTI<span>Laboratorio de Física</span>
        </a>
        <nav aria-label="Espacios de trabajo">
          {school && user?.role === "admin" ? <a href="/admin">Administración</a> : null}
          <a href="/teacher" aria-current={!student ? "page" : undefined}>
            Docente
          </a>
          <a href="/student" aria-current={student ? "page" : undefined}>
            Estudiante
          </a>
        </nav>
        <span className="prototype">
          {school && user
            ? `${user.display_name} · ${user.role}`
            : "Prueba local · datos de ejemplo"}
          {school && user ? (
            <button className="secondary" type="button" onClick={() => void logout()}>
              Cerrar sesión
            </button>
          ) : null}
        </span>
      </header>
      {student ? <Student /> : <Teacher />}
      <footer className="app-footer">
        <span>Colegio Montessori de Sucre · 4.º de secundaria</span>
        <span>Simulación adaptada de PhET Interactive Simulations</span>
      </footer>
    </>
  );
}
