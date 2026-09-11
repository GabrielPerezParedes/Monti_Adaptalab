import test from 'node:test';
import assert from 'node:assert/strict';
import { createVoiceController } from '../src/voice.ts';

function fixture() {
  const instances = [], output = [], states = [], spoken = [];
  class Recognition {
    constructor() { instances.push(this); }
    start() { this.onstart?.(); }
    stop() { this.onend?.(); }
    abort() { this.onend?.(); }
  }
  class Utterance { constructor(text) { this.text = text; } }
  const host = { SpeechRecognition: Recognition, SpeechSynthesisUtterance: Utterance, isSecureContext: true,
    speechSynthesis: { cancel() {}, getVoices: () => [], speak: value => spoken.push(value) } };
  const c = createVoiceController(host, s => states.push(s), text => output.push(text));
  return { c, instances, states, output, spoken };
}
test('microphone is opt-in and repeated final results do not duplicate dictation', () => {
  const { c, instances, output } = fixture();
  assert.equal(instances.length, 0); c.listen('once');
  const e = { resultIndex: 0, results: [{ isFinal: true, 0: { transcript: 'Cambié el ángulo.' } }] };
  instances[0].onresult(e); instances[0].onresult(e);
  assert.deepEqual(output, ['Cambié el ángulo.']); c.dispose();
});
test('continuous mode resumes after silence but stops after denial or explicit stop', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const { c, instances, states } = fixture();
  c.listen('continuous'); instances[0].onend(); t.mock.timers.tick(501);
  assert.equal(instances.length, 2);
  instances[1].onerror({ error: 'not-allowed' }); t.mock.timers.tick(5000);
  assert.equal(instances.length, 2); assert.equal(states.at(-1).mode, 'off');
  c.listen('continuous'); c.stop(); t.mock.timers.tick(5000);
  assert.equal(instances.length, 3); c.dispose();
});
test('speech pauses recognition, resumes continuous mode and disposes pending work', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const { c, instances, spoken, output } = fixture();
  c.listen('continuous'); c.speak('¿Qué cambió en la trayectoria?');
  assert.equal(spoken.length, 1);
  instances[0].onresult({ resultIndex: 0, results: [{ isFinal: true, 0: { transcript: 'eco' } }] });
  assert.equal(output.length, 0); t.mock.timers.tick(5000); assert.equal(instances.length, 1);
  spoken[0].onend(); t.mock.timers.tick(501); assert.equal(instances.length, 2);
  instances[1].onend(); c.dispose(); t.mock.timers.tick(5000); assert.equal(instances.length, 2);
});
