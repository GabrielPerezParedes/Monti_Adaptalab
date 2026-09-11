// Browser speech adapter. Recognition is opt-in and never starts on mount.
export type Mode = 'off' | 'once' | 'continuous';
type Result = { isFinal: boolean; 0: { transcript: string } };
export interface Recognition {
  lang: string; continuous: boolean; interimResults: boolean;
  onstart: (() => void) | null; onend: (() => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onresult: ((e: { resultIndex: number; results: ArrayLike<Result> }) => void) | null;
  start(): void; stop(): void; abort(): void;
}
export type VoiceHost = {
  SpeechRecognition?: new () => Recognition;
  webkitSpeechRecognition?: new () => Recognition;
  speechSynthesis?: SpeechSynthesis;
  SpeechSynthesisUtterance?: new (text: string) => SpeechSynthesisUtterance;
  isSecureContext: boolean;
};
export type VoiceState = { mode: Mode; listening: boolean; speaking: boolean; interim: string; error: string };

export function createVoiceController(host: VoiceHost, update: (s: VoiceState) => void, transcript: (s: string) => void) {
  const Constructor = host.SpeechRecognition || host.webkitSpeechRecognition;
  let state: VoiceState = { mode: 'off', listening: false, speaking: false, interim: '', error: '' };
  let recognition: Recognition | null = null, disposed = false, speakingId = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let pendingSpeech: (() => void) | null = null;
  const publish = (patch: Partial<VoiceState>) => { state = { ...state, ...patch }; if (!disposed) update(state); };
  const clearTimer = () => { clearTimeout(timer); timer = undefined; };
  const resume = () => {
    clearTimer();
    if (!disposed && state.mode === 'continuous' && !state.speaking && !recognition) timer = setTimeout(start, 500);
  };
  function start() {
    if (disposed || !Constructor || recognition || state.mode === 'off' || state.speaking) return;
    const r = new Constructor(); recognition = r;
    const seen = new Set<number>();
    r.lang = 'es-BO'; r.continuous = state.mode === 'continuous'; r.interimResults = true;
    r.onstart = () => { if (recognition === r && !disposed) publish({ listening: true }); };
    r.onresult = e => {
      if (disposed || recognition !== r || state.speaking) return;
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const result = e.results[i];
        if (result.isFinal && !seen.has(i)) { seen.add(i); transcript(result[0].transcript.trim()); }
        else if (!result.isFinal) interim += result[0].transcript;
      }
      publish({ interim });
    };
    r.onerror = e => {
      if (disposed || recognition !== r || e.error === 'aborted') return;
      if (e.error === 'no-speech') return; // continuous mode may resume after silence
      clearTimer();
      const error = ['not-allowed', 'service-not-allowed'].includes(e.error)
        ? 'El micrófono no está autorizado. Habilítalo en el navegador o escribe tu respuesta.'
        : e.error === 'network' ? 'No se pudo conectar el dictado. Puedes reintentarlo o escribir.'
        : 'El dictado no está disponible en este momento. Puedes escribir tu respuesta.';
      publish({ mode: 'off', listening: false, interim: '', error });
      r.abort();
    };
    r.onend = () => {
      if (recognition !== r) return;
      recognition = null;
      publish({ listening: false, interim: '', ...(state.mode === 'once' ? { mode: 'off' } : {}) });
      if (pendingSpeech) { const speak = pendingSpeech; pendingSpeech = null; speak(); }
      else resume();
    };
    try { r.start(); }
    catch { recognition = null; publish({ mode: 'off', listening: false, error: 'No se pudo iniciar el micrófono. Revisa los permisos e inténtalo otra vez.' }); }
  }
  function stopSpeaking() {
    speakingId++; pendingSpeech = null;
    if (state.speaking) host.speechSynthesis?.cancel();
    publish({ speaking: false });
  }
  function listen(mode: Mode) {
    if (disposed) return;
    clearTimer(); stopSpeaking();
    if (mode !== 'off' && (!Constructor || !host.isSecureContext)) {
      publish({ mode: 'off', error: 'Este navegador no permite dictado aquí. Usa localhost o HTTPS y un navegador compatible, o escribe.' }); return;
    }
    // The UI switches modes only after the current recognizer ends.
    if (recognition) { publish({ mode: 'off' }); recognition.stop(); return; }
    publish({ mode, interim: '', error: '' });
    if (mode !== 'off') start();
  }
  function speak(text: string) {
    if (disposed) return;
    const synth = host.speechSynthesis, Utterance = host.SpeechSynthesisUtterance;
    if (!synth || !Utterance) { publish({ error: 'La lectura en voz alta no está disponible. Puedes leer la pregunta.' }); return; }
    clearTimer(); stopSpeaking();
    const id = ++speakingId;
    publish({ speaking: true, interim: '', error: '', mode: state.mode === 'once' ? 'off' : state.mode });
    const play = () => {
      if (disposed || id !== speakingId) return;
      const utterance = new Utterance(text);
      utterance.lang = 'es-BO'; utterance.rate = 0.95;
      const voices = synth.getVoices();
      utterance.voice = voices.find(v => v.lang === 'es-BO') || voices.find(v => v.lang.startsWith('es')) || null;
      const finish = (error = '') => {
        if (disposed || id !== speakingId) return;
        publish({ speaking: false, error }); resume();
      };
      utterance.onend = () => finish();
      utterance.onerror = () => finish('La voz no pudo reproducirse. Puedes volver a pulsar «Escuchar a MONTI».');
      try { synth.speak(utterance); } catch { finish('No se pudo reproducir la voz.'); }
    };
    // Wait until recognition has released the microphone before playing audio.
    if (recognition) { pendingSpeech = play; recognition.abort(); }
    else play();
  }
  function stop() {
    clearTimer(); publish({ mode: 'off', interim: '' }); stopSpeaking();
    recognition?.abort();
  }
  return {
    supported: Boolean(Constructor && host.isSecureContext),
    canSpeak: Boolean(host.speechSynthesis && host.SpeechSynthesisUtterance),
    listen, speak, stop,
    silence: () => { stopSpeaking(); resume(); },
    dispose: () => { disposed = true; stop(); recognition = null; }
  };
}
