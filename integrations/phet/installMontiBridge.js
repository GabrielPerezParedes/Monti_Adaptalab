// SPDX-License-Identifier: GPL-3.0-or-later
// MONTI integration for the public PhET Projectile Motion source build.
// This observes the actual model; it is not the proprietary PhET-iO API.

export default function installMontiBridge(model, ui, win = globalThis.window) {
  const channel = new URLSearchParams(win.location.search).get("montiChannel");
  if (!channel || win.parent === win) return;
  const origin = win.location.origin;
  let lab = null;
  let suppress = false;
  let timer;
  const active = new Map();
  const pending = new Map();
  const properties = {
    speed_m_s: model.initialSpeedProperty,
    angle_deg: model.cannonAngleProperty,
    height_m: model.cannonHeightProperty,
    gravity_m_s2: model.gravityProperty,
    air_resistance: model.airResistanceOnProperty,
  };
  const state = () =>
    Object.fromEntries(
      Object.entries(properties).map(([k, p]) => [k, p.value]),
    );
  const send = (type, payload = {}) =>
    win.parent.postMessage({ type, version: 1, channel, ...payload }, origin);
  const emit = (kind, payload = {}) => {
    if (lab && !suppress)
      send("monti:event", {
        event: { id: win.crypto.randomUUID(), kind, ...payload },
      });
  };
  const publishState = () => send("monti:state", { state: state() });
  const quiet = (fn) => {
    const previous = suppress;
    suppress = true;
    try {
      return fn();
    } finally {
      suppress = previous;
    }
  };
  const flush = () => {
    win.clearTimeout(timer);
    for (const [control, value] of pending) emit("control", { control, value });
    pending.clear();
  };
  const schedule = (control, value) => {
    if (!lab || suppress) return;
    pending.set(control, value);
    win.clearTimeout(timer);
    timer = win.setTimeout(flush, 180);
  };
  const allowed = (key, value) => {
    if (key === "gravity_m_s2") return 10;
    if (key === "air_resistance") return false;
    const constraint = lab.controls[key];
    return constraint.editable
      ? Math.max(constraint.min, Math.min(constraint.max, value))
      : lab.initial[key];
  };
  const enforce = () =>
    quiet(() => {
      for (const [key, prop] of Object.entries(properties))
        prop.value = allowed(key, prop.value);
      model.target.positionProperty.value = lab.target_m;
      model.initialSpeedStandardDeviationProperty.value = 0;
      model.initialAngleStandardDeviationProperty.value = 0;
    });
  const configure = () =>
    quiet(() => {
      model.eraseTrajectories();
      active.clear();
      for (const [key, prop] of Object.entries(properties))
        prop.value = lab.initial[key];
      model.zoomProperty.value = 0.5;
      model.selectedProjectileObjectTypeProperty.value = model.objectTypes[2]; // golf ball
      model.isPlayingProperty.value = true;
      enforce();
      ui.speed.inputEnabled = lab.controls.speed_m_s.editable;
      ui.target.inputEnabled = false;
      ui.projectileControlPanel.inputEnabled = false;
    });

  for (const [key, prop] of Object.entries(properties)) {
    prop.lazyLink((value) => {
      if (!lab || suppress) return;
      if (value !== allowed(key, value)) {
        if (key === "gravity_m_s2" || key === "air_resistance") {
          for (const run_id of active.keys()) emit("invalidated", { run_id });
        }
        // Axon disallows reentrant changes to a property during its notification.
        win.queueMicrotask(() => {
          enforce();
          publishState();
        });
      } else {
        schedule(key, value);
        publishState();
      }
    });
  }
  model.target.positionProperty.lazyLink((value) => {
    if (lab && !suppress && value !== lab.target_m) win.queueMicrotask(enforce);
  });
  for (const [name, prop] of Object.entries(ui.viewProperties)) {
    if (name.endsWith("Property") && typeof prop?.lazyLink === "function")
      prop.lazyLink((value) => schedule(name, value));
  }
  model.isPlayingProperty.lazyLink((value) => emit("pause", { value: !value }));
  model.timeSpeedProperty.lazyLink((value) =>
    schedule("timeSpeed", String(value)),
  );
  model.zoomProperty.lazyLink((value) => schedule("zoom", value));
  model.measuringTape.isActiveProperty.lazyLink((value) =>
    schedule("measuringTape", value),
  );
  model.measuringTape.tipPositionProperty.lazyLink((value) => {
    if (model.measuringTape.isActiveProperty.value) {
      const base = model.measuringTape.basePositionProperty.value;
      schedule(
        "measuringTapeLength_m",
        Math.hypot(value.x - base.x, value.y - base.y),
      );
    }
  });
  model.dataProbe.isActiveProperty.lazyLink((value) =>
    schedule("dataProbe", value),
  );
  model.dataProbe.dataPointProperty.lazyLink((point) => {
    if (point)
      emit("measurement", {
        observed_range_m: point.position.x,
        observed_time_s: point.time,
      });
  });

  const originalFire = model.fireNumProjectiles.bind(model);
  model.fireNumProjectiles = () => {
    if (!lab) return;
    if (active.size) {
      send("monti:error", {
        message:
          "Espera a que termine el lanzamiento o borra la trayectoria para empezar otro.",
      });
      return;
    }
    enforce();
    flush();
    originalFire(1);
  };
  model.trajectoryGroup.elementCreatedEmitter.addListener((trajectory) => {
    if (!lab || suppress) return;
    const run_id = win.crypto.randomUUID();
    active.set(run_id, trajectory);
    emit("launch", { run_id, state: state() });
    trajectory.projectileDataPointProperty.lazyLink((point) => {
      if (point.reachedGround && active.has(run_id)) {
        emit("landed", {
          run_id,
          observed_range_m: point.position.x,
          observed_time_s: point.time,
        });
        active.delete(run_id);
      }
    });
  });
  const originalErase = model.eraseTrajectories.bind(model);
  model.eraseTrajectories = () => {
    if (!suppress) {
      flush();
      emit("erase");
    }
    active.clear();
    originalErase();
  };
  const originalReset = model.reset.bind(model);
  model.reset = () => {
    flush();
    quiet(() => {
      originalReset();
      if (lab) configure();
    });
    emit("reset");
    if (lab) publishState();
  };

  const receive = (event) => {
    if (event.origin !== origin || event.source !== win.parent) return;
    const data = event.data;
    if (
      !data ||
      data.version !== 1 ||
      data.channel !== channel ||
      data.type !== "monti:configure"
    )
      return;
    if (lab) {
      send("monti:configured");
      publishState();
      return;
    }
    const candidate = data.lab;
    if (!validLab(candidate)) {
      send("monti:error", {
        message:
          "La configuración recibida no es compatible con este laboratorio.",
      });
      return;
    }
    lab = candidate;
    configure();
    win.clearInterval(readyTimer);
    send("monti:configured");
    publishState();
  };
  win.addEventListener("message", receive);
  const readyTimer = win.setInterval(() => send("monti:ready"), 1000);
  send("monti:ready");
  return { flush }; // useful for deterministic protocol tests
}

export function validLab(lab) {
  if (!lab || lab.schema_version !== "0.1" || !lab.initial || !lab.controls)
    return false;
  if (lab.initial.gravity_m_s2 !== 10 || lab.initial.air_resistance !== false)
    return false;
  if (!Number.isFinite(lab.target_m) || lab.target_m <= 0 || lab.target_m > 60)
    return false;
  const limits = { speed_m_s: [5, 25], angle_deg: [5, 85], height_m: [0, 15] };
  for (const [key, [min, max]] of Object.entries(limits)) {
    const c = lab.controls[key];
    if (
      !c ||
      typeof c.editable !== "boolean" ||
      ![c.min, c.max, lab.initial[key]].every(Number.isFinite)
    )
      return false;
    if (
      c.min < min ||
      c.max > max ||
      c.min > c.max ||
      lab.initial[key] < c.min ||
      lab.initial[key] > c.max
    )
      return false;
  }
  return true;
}
