import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import install, { validLab } from "../installMontiBridge.js";

class Property {
  constructor(value) {
    this.current = value;
    this.initial = value;
    this.listeners = [];
  }
  get value() {
    return this.current;
  }
  set value(value) {
    if (value !== this.current) {
      this.current = value;
      this.listeners.forEach((fn) => fn(value));
    }
  }
  lazyLink(fn) {
    this.listeners.push(fn);
  }
  reset() {
    this.value = this.initial;
  }
}
const fixture = () => ({
  schema_version: "0.1",
  target_m: 40,
  initial: {
    speed_m_s: 20,
    angle_deg: 20,
    height_m: 0,
    gravity_m_s2: 10,
    air_resistance: false,
  },
  controls: {
    speed_m_s: { min: 5, max: 25, editable: false },
    angle_deg: { min: 5, max: 85, editable: true },
    height_m: { min: 0, max: 0, editable: false },
  },
});
function harness() {
  const messages = [],
    timers = new Map();
  let serial = 0,
    receive,
    created;
  const win = {
    location: {
      search: "?montiChannel=test-channel",
      origin: "http://localhost:5173",
    },
    parent: {
      postMessage: (data, origin) => messages.push({ ...data, origin }),
    },
    crypto: { randomUUID },
    addEventListener: (_, fn) => {
      receive = fn;
    },
    queueMicrotask,
    setTimeout: (fn) => {
      timers.set(++serial, fn);
      return serial;
    },
    clearTimeout: (id) => timers.delete(id),
    setInterval: (fn) => {
      timers.set(++serial, fn);
      return serial;
    },
    clearInterval: (id) => timers.delete(id),
  };
  const props = {
    initialSpeed: 10,
    cannonAngle: 45,
    cannonHeight: 0,
    gravity: 9.8,
    airResistanceOn: false,
    initialSpeedStandardDeviation: 0,
    initialAngleStandardDeviation: 0,
    zoom: 1,
    selectedProjectileObjectType: {},
    isPlaying: true,
    timeSpeed: "normal",
  };
  const model = Object.fromEntries(
    Object.entries(props).map(([k, v]) => [`${k}Property`, new Property(v)]),
  );
  model.objectTypes = [{}, {}, {}];
  model.target = { positionProperty: new Property(15) };
  model.measuringTape = {
    isActiveProperty: new Property(false),
    basePositionProperty: new Property({ x: 0, y: 0 }),
    tipPositionProperty: new Property({ x: 1, y: 0 }),
  };
  model.dataProbe = {
    isActiveProperty: new Property(false),
    dataPointProperty: new Property(null),
  };
  model.trajectoryGroup = {
    elementCreatedEmitter: {
      addListener: (fn) => {
        created = fn;
      },
    },
  };
  const trajectories = [];
  model.fireNumProjectiles = () => {
    const trajectory = {
      projectileDataPointProperty: new Property({ reachedGround: false }),
    };
    trajectories.push(trajectory);
    created(trajectory);
  };
  model.eraseTrajectories = () => {
    trajectories.length = 0;
  };
  model.reset = () => {
    model.eraseTrajectories();
    Object.keys(props).forEach((k) => model[`${k}Property`].reset());
    model.target.positionProperty.reset();
  };
  const ui = {
    speed: {},
    target: {},
    projectileControlPanel: {},
    viewProperties: { totalVelocityVectorOnProperty: new Property(false) },
  };
  const bridge = install(model, ui, win);
  const configure = (lab = fixture(), override = {}) =>
    receive({
      origin: win.location.origin,
      source: win.parent,
      data: {
        type: "monti:configure",
        version: 1,
        channel: "test-channel",
        lab,
      },
      ...override,
    });
  const events = () =>
    messages.filter((m) => m.type === "monti:event").map((m) => m.event);
  return { model, ui, win, messages, configure, events, trajectories, bridge };
}

test("configuration requires the parent, origin, channel and a bounded lab specification", () => {
  const h = harness();
  h.configure(fixture(), { origin: "https://unrelated.invalid" });
  h.configure(fixture(), { source: {} });
  h.configure(fixture(), {
    data: {
      type: "monti:configure",
      version: 1,
      channel: "wrong",
      lab: fixture(),
    },
  });
  assert.equal(h.model.gravityProperty.value, 9.8);
  h.model.fireNumProjectiles();
  assert.equal(h.trajectories.length, 0);
  const invalid = fixture();
  invalid.initial.gravity_m_s2 = 9.8;
  h.configure(invalid);
  assert.equal(h.model.gravityProperty.value, 9.8);
  h.configure();
  assert.equal(h.model.gravityProperty.value, 10);
  assert.equal(h.ui.speed.inputEnabled, false);
  assert.equal(h.ui.target.inputEnabled, false);
  assert.ok(h.messages.every((m) => m.origin === h.win.location.origin));
});

test("a launch records actual initial conditions and emits one landing per run", () => {
  const h = harness();
  h.configure();
  h.model.cannonAngleProperty.value = 45;
  h.model.fireNumProjectiles();
  h.model.fireNumProjectiles(); // simultaneous firing is disabled in this activity
  assert.equal(h.trajectories.length, 1);
  const point = {
    reachedGround: true,
    position: { x: 40, y: 0 },
    time: Math.sqrt(8),
  };
  h.trajectories[0].projectileDataPointProperty.value = point;
  h.trajectories[0].projectileDataPointProperty.value = { ...point };
  const events = h.events();
  assert.equal(events.filter((e) => e.kind === "landed").length, 1);
  assert.deepEqual(
    events.map((e) => e.kind),
    ["control", "launch", "landed"],
  );
  assert.equal(events[1].state.angle_deg, 45);
  assert.equal(events[1].state.gravity_m_s2, 10);
  assert.equal(events[2].run_id, events[1].run_id);
  assert.equal(events[2].observed_range_m, 40);
});

test("fixed variables recover without reentrant writes; reset keeps the assigned objective", async () => {
  const h = harness();
  h.configure();
  h.model.initialSpeedProperty.value = 12;
  h.model.cannonHeightProperty.value = 5;
  await Promise.resolve();
  assert.equal(h.model.initialSpeedProperty.value, 20);
  assert.equal(h.model.cannonHeightProperty.value, 0);
  h.model.fireNumProjectiles();
  h.model.airResistanceOnProperty.value = true;
  await Promise.resolve();
  assert.ok(h.events().some((e) => e.kind === "invalidated"));
  h.model.reset();
  assert.equal(h.model.gravityProperty.value, 10);
  assert.equal(h.model.target.positionProperty.value, 40);
  assert.equal(h.events().filter((e) => e.kind === "reset").length, 1);
  assert.equal(h.events().filter((e) => e.kind === "erase").length, 0);
  h.model.cannonAngleProperty.value = 55;
  h.configure(); // repeated handshakes must not reset the student's work
  assert.equal(h.model.cannonAngleProperty.value, 55);
});

test("measurement and vector controls produce evidence without fabricated scores", () => {
  const h = harness();
  h.configure();
  h.ui.viewProperties.totalVelocityVectorOnProperty.value = true;
  h.model.dataProbe.dataPointProperty.value = { position: { x: 10 }, time: 1 };
  h.bridge.flush();
  assert.ok(
    h
      .events()
      .some(
        (e) =>
          e.control === "totalVelocityVectorOnProperty" && e.value === true,
      ),
  );
  assert.ok(
    h
      .events()
      .some((e) => e.kind === "measurement" && e.observed_range_m === 10),
  );
  assert.ok(h.events().every((e) => !("score" in e)));
  const lab = fixture();
  lab.controls.speed_m_s.max = Infinity;
  assert.equal(validLab(lab), false);
});
