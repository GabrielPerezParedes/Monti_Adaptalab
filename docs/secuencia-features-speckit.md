# Secuencia lógica de features Speckit — MONTI MVP

**Producto:** MONTI · Laboratorios Virtuales Web con Adaptabilidad basada en Agentes Inteligentes  
**Fuentes:** `MONTI_Propuesta_Tecnica_MVP_v1.docx`, `Perfil Tesis.docx`, constitución v1.0.0, baseline `PG_AdaptaLab-2D` 1.1.0  
**Uso:** cada fila `00N-…` se convierte en una feature Speckit (`/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`). No se salta la dependencia “bloquea a”.

---

## 1. Cómo leer este documento

| Columna / símbolo | Significado |
|---|---|
| **ID Speckit** | Nombre de rama/carpeta sugerido: `specs/00N-slug/` |
| **Estado** | `hecho` · `parcial` · `pendiente` · `puerta` (validación humana antes de código) |
| **Aporte** | Qué demuestra ante tribunal / colegio |
| **Comando** | Primer comando Speckit al iniciar esa feature |

**Regla de oro.** La *Propuesta Técnica* y la *Constitución* fijan el MVP. El *Perfil* aporta pregunta de investigación, productos esperados y metodología, pero **no** manda el alcance técnico cuando contradice la propuesta (véase §3).

**Regla Speckit.** Una feature = un incremento comprobable. Si mezcla RAG + voz generativa + auth, se parte. Toda feature de IA debe declarar banderas de alcance honestas (Constitución V).

---

## 2. Norte del MVP (fuente de verdad)

El MVP **sí** entrega:

1. Laboratorio de **movimiento parabólico** para **4.º de secundaria** (Colegio Montessori de Sucre).
2. Generación de **LabSpec** a partir de bibliografía (RAG + validación física en servidor).
3. Experimentación instrumentada sobre simulador **PhET Projectile Motion** (`adapted-from-phet`).
4. Acompañamiento **socrático** (texto, luego voz) anclado a evidencia y fuentes.
5. Evaluación sobre **45 puntos** (18 / 14 / 9 / 4) con revisión docente.
6. Reportes exportables y piloto de clase (~30 sesiones) para la memoria de grado.

El MVP **no** entrega en el primer ciclo: mecánica celeste de primaria, electromagnetismo, motor Phaser propio, cambio automático de dificultad mid-intento, ni PhET-iO.

---

## 3. Aclaraciones del Perfil vs Propuesta (conflictos a resolver)

El Perfil está escrito en un estadio anterior. Antes de features de producto escolar, Speckit debe **formalizar** estas decisiones (feature `001` y, si hace falta, `/speckit-clarify`).

| Tema | Dice el Perfil | Dice la Propuesta / baseline 1.1.0 | Decisión de diseño para Speckit |
|---|---|---|---|
| Temas piloto | Mecánica celeste (primaria) + electromagnetismo (secundaria) | Solo **movimiento parabólico**, 4.º | MVP = parabólico. Otros temas = trabajo futuro en conclusiones |
| Motor gráfico | React + **Phaser.js** / Three.js | React + **PhET** adaptado + puente `postMessage` | PhET. No reescribir motor 2D |
| Adaptabilidad | Ecosistema “adaptativo” amplio | Configuración docente + intervenciones de MONTI según evidencia; **sin** auto-dificultad mid-intento | Adaptabilidad = dificultad elegida + tutor contextual |
| Voz | Whisper / defensa oral automatizada | Primero voz de navegador; luego TTS/STT de proveedor con texto validado | Secuencia: browser → proveedor; texto siempre obligatorio |
| Evaluación | Mejora del aprendizaje vs métodos tradicionales | Artefacto + validación docente + comparación de puntuaciones MONTI vs profesora; pre/post si es viable | No afirmar “mejora de aprendizaje” sin instrumento acordado |
| Persistencia | Implícita / cloud genérico | **Supabase** (PostgreSQL + Auth + pgvector) | Auth y RAG sobre Supabase tras cerrar baseline local |
| Productos 5.x | Dos simuladores + API agente | Un laboratorio + generación + tutor + reportes | Mapear productos del Perfil al backlog de §5 sin duplicar simuladores |
| Tiempo | 4 meses (Gantt) / 6 meses (presupuesto) | ~8 semanas técnicas + piloto | Usar oleadas Speckit (§4); fechas las fija el autor con el tutor |
| Título | Conservar | Conservar | El título del grado **no** cambia; el alcance sí se acota |

**Faltas de aclaración que bloquean features posteriores** (deben quedar resueltas en `001` o en actas adjuntas a la spec):

1. Confirmación escrita de la profesora: rúbrica 18/14/9/4, descriptores 0/50/100 %, tolerancia ±0,5 m, política `E(n)`, fases exploración/evaluación.
2. Ejercicios del cap. 8 RACSO admitidos (p. ej. orientación 8.7 / 8.9 / 8.11) y convención `g = 10 m/s²`.
3. Tamaño real del piloto (¿30?) y si las cuentas serán provisión MONTI o credenciales del colegio.
4. Límite de presupuesto API (texto, embeddings, voz) y cuentas OpenAI/Supabase.
5. Plantilla UPB / observaciones del tutor para memoria (no bloquea código, sí documentación).
6. Política de datos: retención de diálogos, descarte de audio tras transcribir, acceso RLS por curso.

---

## 4. Oleadas (orden lógico)

```text
Oleada A  Cerrar baseline y gobernanza pedagógica
          └─ 001 → 002 → 003

Oleada B  Identidad escolar y datos de producción
          └─ 004 → 005

Oleada C  Aporte central: RAG + generación verificable
          └─ 006 → 007

Oleada D  Aporte central: tutoría socrática y calificación con evidencia
          └─ 008 → 009

Oleada E  Experiencia de aula: personaje, voz generativa, reportes
          └─ 010 → 011

Oleada F  Piloto, carga y defensa
          └─ 012 → 013 → 014
```

**Por qué este orden**

- Sin **rúbrica/tolerancias validadas** (003), la IA no puede calificar con legitimidad.
- Sin **auth + PostgreSQL** (004–005), RAG y piloto escolar no son defendibles.
- **RAG antes que tutor LLM**: el tutor sin corpus curado alucina; viola el Perfil y la Constitución V.
- **Tutor de texto antes que voz generativa**: el texto es la fuente de verdad del audio.
- **Carga de 30** después de IA: medir costo/latencia con el stack real, no con el prototipo local.

---

## 5. Backlog Speckit (secuencia canónica)

### Oleada A — Cerrar baseline y gobernanza pedagógica

#### `001-alcance-mvp-y-reconciliacion-perfil`

| | |
|---|---|
| **Estado** | `puerta` |
| **Tipo** | Spec + decisiones (poca o nula UI) |
| **Objetivo** | Documento de alcance MVP que reconcilia Perfil ↔ Propuesta ↔ Constitución ↔ código 1.1.0 |
| **Entrega** | Spec aprobada: tema único, exclusiones, mapa objetivos→features, lista de aclaraciones §3 con dueño (autor / profesora / tutor) |
| **Bloquea a** | 002+ |
| **Comando** | `/speckit-specify` luego `/speckit-clarify` si quedan huecos |
| **Criterio de cierre** | Ninguna contradicción abierta sobre tema, motor, rúbrica ni auth; exclusiones explícitas (Phaser, electromagnetismo, auto-dificultad) |

#### `002-cierre-integracion-tecnica-visual`

| | |
|---|---|
| **Estado** | `parcial` (API/puente/física ya existen; falta recorrido visual completo) |
| **Objetivo** | Cerrar hito 1: recorrido manual de `docs/validacion.md` con PhET real en navegador |
| **Entrega** | Checklist ejecutado (espera→publicar→explorar→evaluar→entregar→revisar→exportar); bugs de integración corregidos; evidencia en `docs/validacion.md` |
| **Depende de** | 001 |
| **Bloquea a** | 003, 012 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Los 7 pasos del recorrido manual pasan en al menos un navegador de referencia; `npm run build`, `test:bridge`, `test:voice`, `pytest` en verde |

#### `003-validacion-docente-rubrica-y-politica`

| | |
|---|---|
| **Estado** | `puerta` |
| **Objetivo** | Convertir `45-v1-draft` y `attempt_policy draft-1` en versiones **aceptadas** por la profesora |
| **Entrega** | Acta/spec con: descriptores 0/50/100 %, ejemplos de explicación aceptable/rechazable, tolerancia ±0,5 m, `E(n)`, tratamiento de fallos técnicos; bump de `rubric_version` / `attempt_policy.version` en LabSpec |
| **Depende de** | 001, 002 |
| **Bloquea a** | 007, 008, 009, 011, 013 |
| **Comando** | `/speckit-specify` (+ checklist `/speckit-checklist`) |
| **Criterio de cierre** | Firma/confirmación docente; código usa versiones no-`draft` o documenta excepción temporal explícita |

---

### Oleada B — Identidad escolar y datos

#### `004-supabase-auth-roles-y-postgresql`

| | |
|---|---|
| **Estado** | `pendiente` |
| **Objetivo** | Sustituir clave docente de desarrollo y SQLite local por identidad escolar |
| **Entrega** | Supabase Auth; roles docente/estudiante; PostgreSQL; migraciones; RLS por curso; HTTPS en entorno piloto; retiro de `MONTI_DEV_TEACHER_KEY` del flujo de aula |
| **Depende de** | 001 |
| **Bloquea a** | 005, 006, 012, 013 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Estudiante no ve borradores ni intentos ajenos; docente solo su curso; health/mode ya no es solo `local-prototype` para el despliegue piloto |

#### `005-modelo-datos-academico-y-auditoria`

| | |
|---|---|
| **Estado** | `parcial` (esquema SQLite existe) |
| **Objetivo** | Modelo académico completo: cursos, sesiones, LabSpec versionado, eventos, diálogos, revisiones, reportes |
| **Entrega** | Migraciones; historial de revisiones con motivo de override; jobs/reintentos para generación y reportes; políticas de retención acordadas |
| **Depende de** | 004 |
| **Bloquea a** | 006, 009, 011 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Toda calificación y diálogo quedan auditables; recarga recupera estado de servidor |

---

### Oleada C — RAG y generación verificable (aporte central 1)

#### `006-corpus-racso-cap8-e-indice-rag`

| | |
|---|---|
| **Estado** | `pendiente` |
| **Objetivo** | Corpus curado del capítulo 8 (teoría + problemas; resoluciones con acceso diferenciado) |
| **Entrega** | Fragmentos con `obra_id`, página impresa, página PDF, sección, tipo, versión; embeddings (`text-embedding-3-small` o sucesor fijado); pgvector; pruebas de recuperación y atribución; corrección OCR conocida (p. ej. 8.8: 720 vs 120 km/h) |
| **Depende de** | 003 (ejercicios admitidos), 004 |
| **Bloquea a** | 007, 008 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Consultas de evaluación recuperan fuentes pertinentes; cero cifras críticas sin contraste con original; PDF completo **fuera** del repo público |

#### `007-generacion-labspec-rag-y-validador`

| | |
|---|---|
| **Estado** | `parcial` (hoy: generador paramétrico reproducible) |
| **Objetivo** | LabSpec desde RAG + Structured Outputs, **siempre** pasado por validador físico de servidor |
| **Entrega** | Pipeline: recuperar → componer LabSpec → validar rangos/unidades/solución testigo → preview docente → publicar; conservar seed, fuentes, `schema_version`, rúbrica y tolerancias; el modelo **nunca** ejecuta código |
| **Depende de** | 003, 006, 005 |
| **Bloquea a** | 008, 013 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | N configs con seeds distintos producen escenas/controles coherentes; insoluble/inválido no publica; testigo nunca en payload público; banderas `rag: true` solo cuando el pipeline esté activo |

---

### Oleada D — Tutoría socrática y calificación (aporte central 2)

#### `008-tutor-socratico-textual-contextual`

| | |
|---|---|
| **Estado** | `parcial` (hoy: prompts por reglas) |
| **Objetivo** | MONTI pregunta en texto usando objetivo, eventos, explicaciones previas y fragmentos RAG |
| **Entrega** | Una pregunta a la vez; momentos duda/error/acierto/transferencia; ayudas progresivas; registro de comprensión con referencias; fallback si falla el proveedor; simulador usable mientras espera |
| **Depende de** | 006, 007, 002 |
| **Bloquea a** | 009, 010 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Banco inicial ≥20 situaciones revisadas por la profesora (pertinencia, apertura, progresión, apoyo científico); modo `rule-based-guide` queda como degradación, no como “IA” |

#### `009-valoracion-asistida-y-override-docente`

| | |
|---|---|
| **Estado** | `parcial` (físico + eficiencia en servidor; procedimiento/comprensión manual) |
| **Objetivo** | MONTI propone 18 y 14 con criterio, evidencia y explicación; la profesora confirma o corrige |
| **Entrega** | Propuestas acotadas a rúbrica versionada; override con motivo; comparación profesora↔MONTI por criterio; total ≤45; pedir ayuda a MONTI **no** penaliza |
| **Depende de** | 003, 008, 005 |
| **Bloquea a** | 011, 013 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Ninguna nota pedagógica se publica sin rastro de evidencia; resultado físico sigue siendo solo del servidor |

---

### Oleada E — Aula: personaje, voz, reportes

#### `010-personaje-definitivo-y-voz-generativa`

| | |
|---|---|
| **Estado** | `parcial` (robot provisional + voz del navegador) |
| **Objetivo** | Personaje con estados (reposo/escucha/espera/habla/señalización) y voz de proveedor sobre **texto ya validado** |
| **Entrega** | Sprite/animación que no tape controles; pulsar-para-hablar; revisión de transcripción; TTS de respuesta validada; alternativa escrita siempre; no persistir audio; HTTPS + permisos |
| **Depende de** | 008, 004 |
| **Bloquea a** | 012, 013 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Si falla micrófono/red, el estudiante completa por texto; `generative_voice` solo se enciende cuando el flujo esté listo; `prefers-reduced-motion` respetado |

#### `011-reportes-pdf-csv-y-resumen-fiel`

| | |
|---|---|
| **Estado** | `parcial` (export `.txt` existe) |
| **Objetivo** | Resumen individual PDF + consolidado docente CSV/lista, fiel a evidencia |
| **Entrega** | Identificación, resultado verificado, resumen 3–5 oraciones (≤150 palabras), desglose /45, estado provisional si hubo fallo técnico; misma versión para estudiante y profesora |
| **Depende de** | 005, 009 |
| **Bloquea a** | 013 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Afirmaciones del reporte trazables a eventos/diálogos; sin interpretación inventada |

---

### Oleada F — Piloto, carga y defensa

#### `012-resiliencia-reconexion-y-carga-30`

| | |
|---|---|
| **Estado** | `pendiente` |
| **Objetivo** | Clase simultánea viable: 30 sesiones, ráfagas de preguntas/voz, recuperación |
| **Entrega** | Prueba de carga documentada (errores, latencia p50/p95, costo/sesión); cola de eventos sin duplicar; límites de tokens; degradación graceful de IA |
| **Depende de** | 004, 008, 010 |
| **Bloquea a** | 013 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Criterios de aceptación de carga acordados y medidos; no se declara “listo para aula” sin este registro |

#### `013-piloto-colegio-e-instrumentos-de-evaluacion`

| | |
|---|---|
| **Estado** | `pendiente` |
| **Objetivo** | Piloto real con instrumentos mixtos (Perfil §4) y evidencia para memoria |
| **Entrega** | Protocolo de piloto; consentimiento/datos; usabilidad; comparación de puntuaciones; (si viable) pre/post; limitaciones explícitas; **no** sobreclamar mejora de aprendizaje |
| **Depende de** | 003, 007, 009, 011, 012 |
| **Bloquea a** | 014 |
| **Comando** | `/speckit-specify` |
| **Criterio de cierre** | Dataset y análisis mínimos para capítulos de validación de la tesis |

#### `014-documentacion-defensa-y-manuales`

| | |
|---|---|
| **Estado** | `pendiente` |
| **Objetivo** | Cerrar productos 5.1–5.5 del Perfil con la verdad del MVP construido |
| **Entrega** | SRS final alineado; arquitectura C4 actualizada; manuales docente/estudiante/admin; memoria según plantilla UPB; limitaciones y trabajos futuros (5.º/6.º, otros temas) |
| **Depende de** | 013 |
| **Comando** | `/speckit-specify` (docs) o trabajo paralelo documentado |
| **Criterio de cierre** | Narrativa de tesis = comportamiento real del sistema (banderas de alcance coherentes) |

---

## 6. Mapa Perfil → Features (trazabilidad de productos)

| Producto esperado (Perfil) | Features que lo materializan en el MVP real |
|---|---|
| 5.1 SRS + análisis de infraestructura | `001`, `002`, `014` |
| 5.2 Arquitectura + modelo vectorial | `001`, `005`, `006`, `014` |
| 5.3 Módulo de simulación web beta | `002` + baseline PhET 1.1.0 (**no** Phaser ni dos temas) |
| 5.4 API del agente socrático + voz | `007`, `008`, `009`, `010` |
| 5.5 Validación + documentación | `012`, `013`, `014` |

| Objetivo específico (Perfil) | Cobertura MVP |
|---|---|
| Diagnosticar deficiencias / requerimientos | `001`, `003`, entrevistas ya previstas |
| Diseñar arquitectura y flujos RAG | `001`, `005`, `006`, `007` |
| Desarrollar simuladores mecánica y EM | **Reinterpretado:** un laboratorio de parabólico; EM/celeste → fuera de MVP |
| Agente socrático + voz | `008`, `009`, `010` |
| Validar con piloto | `012`, `013` |

---

## 7. Baseline ya construido (no volver a “especificar” como greenfield)

Tratar como **plataforma existente** al escribir specs nuevas. Extender; no reinventar.

| Capacidad 1.1.0 | Ubicación típica | Feature que la supera |
|---|---|---|
| Teacher / Student pages, publicación, espera | `apps/web` | 004 (auth), 007 (preview RAG) |
| PhET + puente + eventos idempotentes | `integrations/phet`, `PhETLab.tsx` | 002 (cierre visual) |
| Generador paramétrico + testigo privado | `generation.py` | 007 |
| Física independiente + eficiencia `E(n)` | `physics.py` | 003 (versión aceptada) |
| Rúbrica 45 con review humano | `main.py` | 009 |
| Prompts por reglas | `/prompt` | 008 |
| Voz navegador + compañero provisional | `voice.ts`, `MontiCompanion.tsx` | 010 |
| Export `.txt` | reportes API | 011 |
| SQLite local + teacher key | `database.py` | 004 |

---

## 8. Dependencias (vista compacta)

```text
001 ─┬─► 002 ─► 003 ─┬─► 006 ─► 007 ─► 008 ─┬─► 009 ─► 011 ─┐
     │               │                      │               │
     └─► 004 ─► 005 ─┴──────────────────────┴─► 010         │
              │                                              ▼
              └────────────────────────► 012 ──────────► 013 ─► 014
```

**Camino crítico hacia el aporte de grado:**  
`001 → 003 → 004 → 006 → 007 → 008 → 009 → 013`

**Camino crítico hacia el aula:**  
`001 → 002 → 004 → 010 → 012 → 013`

---

## 9. Protocolo de ejecución con Speckit

Para **cada** ID `00N-…`:

1. `/speckit-specify` — historias priorizadas P1…Pn, escenarios Given/When/Then, bordeados por Constitución.
2. `/speckit-clarify` — solo si hay ambigüedad que bloquee el plan (máx. foco en puertas 001/003).
3. `/speckit-plan` — Constitution Check obligatorio; stack y contratos.
4. `/speckit-tasks` — tareas ordenadas por dependencia.
5. `/speckit-analyze` — si el cruce spec/plan/tasks muestra huecos.
6. `/speckit-implement` — ejecutar tareas; no declarar hechos capacidades con bandera en falso.
7. `/speckit-checklist` — útil en 002, 003, 012, 013.

**Definition of Done transversal**

- [ ] Spec distingue *ya construido* vs *a construir*
- [ ] Constitution Check en verde o enmienda explícita
- [ ] Pruebas automatizadas pertinentes en verde
- [ ] Banderas de health/alcance coherentes con la realidad
- [ ] Sin filtrar solución testigo ni audio crudo al cliente
- [ ] Docs de hito actualizados si cambió el comportamiento público

---

## 10. Qué hacer ahora (siguiente acción recomendada)

1. Ejecutar **`/speckit-specify`** para `001-alcance-mvp-y-reconciliacion-perfil` usando este documento como input.
2. En paralelo operativo (fuera de código): agendar con la profesora la sesión de **`003`** (rúbrica y política).
3. No abrir `006+` hasta tener 001+003 cerradas y 004 al menos especificada.

---

## 11. Referencias internas

| Documento | Rol |
|---|---|
| `.specify/memory/constitution.md` | Normas no negociables |
| `docs/MONTI_Propuesta_Tecnica_MVP_v1.docx` | Diseño MVP y rúbrica |
| `docs/Perfil Tesis.docx` | Pregunta, productos, metodología; requiere reconciliación |
| `docs/plan-desarrollo.md` | Hitos 1–7 (esta secuencia los concreta en features) |
| `docs/arquitectura.md` | Frontera servidor/cliente y eventos |
| `docs/validacion.md` | Checklist técnico del hito 1 |
| `README.md` | Estado real 1.1.0 |

---

*Documento de planificación Speckit. No sustituye una feature spec ni enmienda la constitución. Versión 1.0 — 2026-09-10.*
