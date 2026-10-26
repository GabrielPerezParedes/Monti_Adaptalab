# Alcance técnico del MVP — MONTI

**Estado**: Publicado (cierre operativo del autor)  
**Fecha**: 2026-10-25  
**Feature Speckit**: `specs/002-alcance-mvp-y-reconciliacion-perfil/` (ítem canónico `001-alcance-mvp-y-reconciliacion-perfil` en la secuencia)

Este archivo es la **fuente canónica** del alcance técnico del MVP. La memoria de grado y las features Speckit posteriores deben citarlo. El cierre operativo basta con decisión y commit del autor; el tutor revisa el alcance en la memoria final (no es puerta previa). La profesora no firma este documento (su puerta es la validación de rúbrica/política).

---

## 1. Título y propósito

Definir, de forma defendible ante colegio y tribunal, **qué entra y qué no entra** en el MVP de MONTI: tema, motor, evaluación, identidad de aula, proposición de valor y trazabilidad Perfil → features — reconciliando Perfil de tesis, Propuesta Técnica MVP, Constitución y baseline `PG_AdaptaLab-2D` 1.1.0.

---

## 2. Precedencia de fuentes

| Conflicto | Prevalece |
|-----------|-----------|
| Tema, motor, exclusiones, evaluación, frontera de IA | **Propuesta Técnica MVP** + **Constitución** (`.specify/memory/constitution.md`) |
| Título del grado y pregunta de investigación | **Perfil** (se conservan) |
| Productos 5.x del Perfil vs backlog real | Se **reinterpretan** vía el mapa de este documento (no se duplican simuladores ni se promete Phaser) |

El Perfil está escrito en un estadio anterior; no manda el alcance técnico cuando contradice Propuesta/Constitución.

---

## 3. Inclusiones del MVP

| Dimensión | Decisión |
|-----------|----------|
| Tema | Movimiento **parabólico** |
| Curso / colegio | **4.º de secundaria**, Colegio Montessori de Sucre |
| Motor | **PhET Projectile Motion**, marca `adapted-from-phet`, puente `postMessage` |
| Evaluación | Rúbrica **45** puntos (`45-v1`): procedimiento 18, comprensión 14, resultado físico 9, evidencia de aprendizaje 4 — acta `docs/acta-rubrica-profesora.md` |
| Tolerancia de objetivo | **±0,5 m** |
| Convención física | SI; **`g = 10 m/s²`**; sin resistencia del aire |
| Política de intentos | Versionada `1.0` (aceptada); `E(n)` dentro de evidencia de aprendizaje |
| Adaptabilidad | Configuración docente + tutor contextual; **sin** auto-cambio de dificultad mid-intento |
| Voz | Primero voz del **navegador**; luego TTS/STT de proveedor; el **texto validado** es fuente de verdad del audio |
| Persistencia de producto | Camino escolar: PostgreSQL + identidad de producción (p. ej. Supabase Auth); SQLite = desarrollo |

---

## 4. Exclusiones explícitas

Fuera del MVP (trabajo futuro / conclusiones, no entrega del ciclo):

1. Electromagnetismo (secundaria) como tema piloto  
2. Mecánica celeste de primaria como tema piloto  
3. Motor propio **Phaser.js** / Three.js en lugar de PhET  
4. Auto-cambio de dificultad **mid-intento**  
5. **PhET-iO** y telemetría asociada  
6. Afirmar **mejora causal del aprendizaje** sin instrumento acordado  

---

## 5. Proposición de valor (lenguaje admitido)

MONTI aporta un **laboratorio** en el que cada estudiante cuenta con acompañamiento tipo **tutor socrático** que **realimenta** el aprendizaje previo hecho en clase. El sistema está pensado para estar disponible en cada computador: escuchar dudas (voz) y responder (audio y texto) **según las features de voz ya entregadas o planificadas**, con banderas de health honestas.

En el aula, eso permite **acompañar, guiar y evaluar en paralelo** a muchos estudiantes —algo que una sola profesora no puede hacer en simultáneo—. El aporte defendible es:

1. Acompañamiento individualizado y realimentación del aprendizaje de clase  
2. **Evidencia** inspectable de comprensión y de procedimiento  
3. **Evaluación asistida**: MONTI puntúa los **cuatro** criterios con telemetría PhET + diálogo + física de **servidor**; exporta **informe por alumno**; la profesora **carga a registros** el puntaje MONTI (acuerdo acta 2026-10-26). Contraste con Ser/Hacer ocurre **fuera** del laboratorio.  
4. Si el piloto genera datos: contraste del informe MONTI con otras rúbricas del trimestre (Ser/Hacer), no como override obligatorio dentro del producto  

**Prohibido** en memoria y docs públicos: afirmar que el proyecto **mejora el aprendizaje** como efecto causal demostrado.

---

## 6. Ya construido vs a construir

| Capacidad | Estado | Notas / honestidad |
|-----------|--------|---------------------|
| Lab PhET + puente + eventos | **Hecho** (baseline 1.1.0) | Recorrido visual hito 1 cerrado — `docs/validacion.md` (2026-10-25) |
| Generador paramétrico + física servidor | **Hecho** | No es RAG |
| Rúbrica 45 + informe MONTI | **Hecho** (`45-v1`) | Acta cerrada; carga a registros sin override obligatorio |
| Preguntas por reglas + voz navegador | **Hecho** (prototipo) | No es tutor LLM ni voz generativa |
| Auth escolar local (roles, grados, asignaturas) | **Hecho (prototipo)** | `specs/001-school-auth-roles/`; flag `school_auth`; **no** es IdP del colegio |
| Cuentas institucionales + Postgres/RLS/HTTPS | **Pendiente** | Identidad de producción / Oleada B restante |
| RAG + LabSpec desde bibliografía | **Pendiente** | Banderas `rag` en falso hasta entonces |
| Tutor LLM socrático | **Pendiente** | Tras corpus + rúbrica aceptada |
| Voz generativa de proveedor | **Pendiente** | Tras tutor de texto; `generative_voice` en falso |
| Piloto ~30 / carga validada | **Pendiente** | Meta de diseño; concurrencia aún no medida |

---

## 7. Mapa Perfil → features

### Productos esperados (Perfil 5.x)

| Producto (Perfil) | Features (canónicas / carpetas repo) | Estado MVP |
|-------------------|--------------------------------------|------------|
| 5.1 SRS + infraestructura | Alcance (`docs/alcance-mvp.md` / `specs/002-…`); cierre visual; docs finales (`014`) | Parcial — alcance **publicado** |
| 5.2 Arquitectura + modelo vectorial | Alcance; modelo datos (`005`); corpus RAG (`006`); docs (`014`) | Pendiente (arquitectura baseline existe) |
| 5.3 Simulación web beta | Baseline PhET 1.1.0 + cierre visual (`002` canónico → carpeta `003-…` cuando se abra) | Parcial — **un** lab parabólico (**no** dos temas ni Phaser) |
| 5.4 API agente socrático + voz | Generación (`007`), tutor (`008`), valoración (`009`), voz (`010`) | Pendiente |
| 5.5 Validación + documentación | Piloto/carga (`012`–`013`), docs (`014`) | Pendiente |

### Objetivos específicos (Perfil) — cobertura MVP

| Objetivo | Cobertura |
|----------|-----------|
| Diagnosticar / requerimientos | Este alcance + rúbrica docente + entrevistas |
| Arquitectura y flujos RAG | `005`–`007` (tras rúbrica e identidad de producción) |
| “Simuladores” mecánica y EM | **Reinterpretado:** un laboratorio de parabólico; EM/celeste → fuera de MVP |
| Agente socrático + voz | `008`–`010` |
| Validar con piloto | `012`–`013` (~30 sesiones) |

**Auth:** `specs/001-school-auth-roles/` = avance **parcial** de Oleada B / ítem canónico `004` (SQLite + first-party). Falta Supabase/Postgres/RLS/HTTPS y cuentas del colegio.

**Orden:** RAG / tutor LLM **después** de rúbrica aceptada y corpus; no marcarlos hechos mientras las banderas de health estén en falso.

---

## 8. Piloto e identidad

| Tema | Decisión |
|------|----------|
| Meta de diseño | **~30** sesiones de estudiante (carga, demos, narrativa) |
| Logística | El colegio confirma fechas/cupo sin invalidar la meta de planificación |
| Cuentas en el aula | **Institucionales del colegio** (correo/IdP) desde el piloto |
| Auth local (`001-school-auth-roles`, seed admin) | Solo **desarrollo / demos**; **no** es el modelo de cuentas del piloto |
| Producción | Identidad acordada (p. ej. Supabase Auth) + PostgreSQL + RLS + HTTPS |

---

## 9. Aclaraciones abiertas

| Tema | Dueño | Bloquea (ejemplos) |
|------|-------|---------------------|
| (cerrada) Rúbrica `45-v1` + política `1.0` | — | Ver `docs/acta-rubrica-profesora.md` y `specs/004-…` |
| Presupuesto / cuentas API (texto, embeddings, voz) | Autor | Activar banderas de IA en entorno real |
| Política de datos (retención diálogos, audio, RLS) | Autor + colegio | Cierre de identidad de producción y piloto |
| Plantilla UPB / observaciones del tutor (memoria) | Tutor / autor | Documentación final (no bloquea código de lab) |

**Ya decidido (no reabrir como “abierto”):** cuentas del colegio; meta ~30 sesiones; tema parabólico; motor PhET; `g = 10`.

---

## 10. Referencias

| Documento | Rol |
|-----------|-----|
| `.specify/memory/constitution.md` | Normas no negociables |
| `docs/secuencia-features-speckit.md` | Backlog Speckit / oleadas |
| `docs/continuar-speckit.md` | Guía operativa de comandos |
| `docs/acta-rubrica-profesora.md` | Acuerdo rúbrica Saber/45, telemetría MONTI e informe por alumno |
| `specs/002-alcance-mvp-y-reconciliacion-perfil/spec.md` | Spec de esta feature |
| `specs/002-alcance-mvp-y-reconciliacion-perfil/plan.md` | Plan de implementación documental |
| `specs/001-school-auth-roles/` | Auth local (prototipo) |
| `docs/validacion.md` | Checklist hito 1 / recorrido PhET |
| `docs/validacion-auth-001.md` | Evidencia quickstart auth local |
| `README.md` | Estado del hito de código |
| `docs/Perfil Tesis.docx` / Propuesta Técnica MVP | Fuentes reconciliadas aquí |
