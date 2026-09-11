import { useEffect, useRef, useState } from 'react';
import type { FormEvent, PointerEvent } from 'react';
import { createVoiceController } from './voice';
import type { VoiceHost, VoiceState } from './voice';

type Props = {
  prompt: string; answer: string; busy: boolean; saved: boolean;
  onAnswer: (value: string) => void; onTranscript: (value: string) => void;
  onSave: (event: FormEvent) => void;
};

export default function MontiCompanion(props: Props) {
  const root = useRef<HTMLDivElement>(null);
  const callbacks = useRef(props); callbacks.current = props;
  const controller = useRef<ReturnType<typeof createVoiceController> | null>(null);
  const [voice, setVoice] = useState<VoiceState>({ mode: 'off', listening: false, speaking: false, interim: '', error: '' });
  const [supported, setSupported] = useState(false), [canSpeak, setCanSpeak] = useState(false);
  const [open, setOpen] = useState(true), [position, setPosition] = useState({ x: 76, y: 50 });
  const drag = useRef({ x: 0, y: 0, left: 0, top: 0, moved: false });

  function clamp(x: number, y: number) {
    const node = root.current, parent = node?.parentElement;
    if (!node || !parent) return { x, y };
    return { x: Math.max(8, Math.min(x, parent.clientWidth - node.offsetWidth - 8)),
      y: Math.max(8, Math.min(y, parent.clientHeight - node.offsetHeight - 8)) };
  }
  useEffect(() => {
    const c = createVoiceController(window as unknown as VoiceHost, setVoice, text => callbacks.current.onTranscript(text));
    controller.current = c; setSupported(c.supported); setCanSpeak(c.canSpeak);
    const pause = () => { if (document.hidden) c.stop(); };
    const leave = () => c.stop();
    document.addEventListener('visibilitychange', pause); window.addEventListener('pagehide', leave);
    return () => { c.dispose(); controller.current = null; document.removeEventListener('visibilitychange', pause); window.removeEventListener('pagehide', leave); };
  }, []);
  useEffect(() => {
    const observer = new ResizeObserver(() => setPosition(p => clamp(p.x, p.y)));
    if (root.current) { observer.observe(root.current); observer.observe(root.current.parentElement!); }
    return () => observer.disconnect();
  }, []);

  function begin(e: PointerEvent<HTMLButtonElement>) {
    if (e.button !== 0) return;
    drag.current = { x: e.clientX, y: e.clientY, left: position.x, top: position.y, moved: false };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function move(e: PointerEvent<HTMLButtonElement>) {
    if (!e.currentTarget.hasPointerCapture(e.pointerId)) return;
    const d = drag.current, dx = e.clientX - d.x, dy = e.clientY - d.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) d.moved = true;
    if (d.moved) setPosition(clamp(d.left + dx, d.top + dy));
  }
  const active = voice.mode !== 'off';
  const status = voice.speaking ? 'Hablando' : voice.listening ? 'Te escucho' : active ? 'Conectando micrófono…' : 'Estoy aquí para ayudarte';
  return <div ref={root} className={`monti-companion ${voice.listening ? 'is-listening' : ''} ${voice.speaking ? 'is-speaking' : ''}`} style={{ left: position.x, top: position.y }}>
    <div className="companion-handle">
      <button type="button" className="companion-character" aria-label="MONTI: abrir o cerrar. Arrastra para mover; también puedes usar las flechas." aria-expanded={open}
        onPointerDown={begin} onPointerMove={move}
        onPointerUp={e => e.currentTarget.releasePointerCapture(e.pointerId)}
        onClick={e => { if (e.detail === 0 || !drag.current.moved) setOpen(v => !v); }}
        onKeyDown={e => { const delta: Record<string, number[]> = { ArrowLeft: [-20, 0], ArrowRight: [20, 0], ArrowUp: [0, -20], ArrowDown: [0, 20] }; if (delta[e.key]) { e.preventDefault(); const [x, y] = delta[e.key]; setPosition(p => clamp(p.x + x, p.y + y)); } }}>
        <span className="companion-emoji" aria-hidden="true">🤖</span>
      </button>
      <div className="companion-name"><strong>MONTI</strong><span role="status">{status}</span></div>
      {active && <button type="button" className="companion-stop" onClick={() => controller.current?.stop()} aria-label="Apagar micrófono y voz">■</button>}
    </div>
    {open && <section className="companion-bubble" aria-label="Conversación con MONTI">
      <div className="companion-bubble-top"><span>Exploremos tu idea</span><button type="button" aria-label="Minimizar MONTI" onClick={() => setOpen(false)}>−</button></div>
      <p className="companion-prompt">{props.prompt}</p>
      <div className="voice-controls">
        <button type="button" disabled={!supported || props.busy || (active && voice.mode !== 'once')} aria-pressed={voice.mode === 'once'} onClick={() => controller.current?.listen(active ? 'off' : 'once')}>{voice.mode === 'once' ? 'Terminar de hablar' : 'Hablar una vez'}</button>
        <button type="button" disabled={!supported || props.busy || (active && voice.mode !== 'continuous')} aria-pressed={voice.mode === 'continuous'} onClick={() => controller.current?.listen(active ? 'off' : 'continuous')}>{voice.mode === 'continuous' ? 'Apagar escucha continua' : 'Escucha continua'}</button>
        <button type="button" disabled={!canSpeak} onClick={() => voice.speaking ? controller.current?.silence() : controller.current?.speak(props.prompt)}>{voice.speaking ? 'Detener voz' : 'Escuchar a MONTI'}</button>
      </div>
      {!supported && <p className="voice-note">El dictado no está disponible aquí. Puedes escribir tu explicación.</p>}
      {voice.error && <p className="voice-error" role="alert">{voice.error}</p>}
      {voice.interim && <p className="voice-interim">{voice.interim}</p>}
      <form onSubmit={e => { controller.current?.stop(); props.onSave(e); }}>
        <label>Tu explicación<textarea value={props.answer} onChange={e => props.onAnswer(e.target.value)} maxLength={2000} required rows={3} placeholder="Habla o escribe: cambié… porque…" /></label>
        <button className="primary" disabled={props.busy || !props.answer.trim()}>Guardar explicación</button>
        {props.saved && <p className="voice-note" role="status">Explicación guardada.</p>}
      </form>
      <p className="voice-note">Revisa el dictado antes de guardarlo. El navegador puede procesar el audio en un servicio externo.</p>
      <p className="companion-source">RACSO · Cap. 8 · g = 10 m/s²</p>
    </section>}
  </div>;
}
