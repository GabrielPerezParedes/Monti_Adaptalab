# Acta de rúbrica docente — laboratorio MONTI (Saber / 45)

**Estado**: Cerrada / aceptada (Speckit `004-validacion-docente-rubrica-y-politica`)  
**Fecha de acuerdo**: 2026-10-26 · **Cierre formal**: 2026-10-26  
**Colegio**: Colegio Montessori de Sucre  
**Profesora de referencia**: Carla Lizet  
**Versiones**: `rubric_version = 45-v1` · `attempt_policy.version = 1.0`  
**Clave de score (4.º criterio)**: `learning_evidence` (máx. 4). Alias de lectura legacy: `efficiency` en datos `45-v1-draft`.

Este documento fija **cómo se califica el laboratorio MONTI-PhET** dentro del trimestre escolar y qué debe hacer MONTI para que la profesora pueda **cargar la nota a sus registros** con confianza.

---

## 1. Encaje con el sistema de calificaciones del colegio

| Campo | Puntos del trimestre | Rol del laboratorio MONTI |
|-------|----------------------|---------------------------|
| **Ser** | 15 | Fuera del laboratorio; otras rúbricas / observación de la profesora |
| **Hacer** | 40 | Fuera del laboratorio; ~6 casillas (tareas, prácticas del trimestre) |
| **Saber** | 45 | Varias casillas (~3–4): exámenes papel, defensas, **y este laboratorio** |

El laboratorio MONTI es **una casilla del SABER**. La devolutiva del proyecto de grado sobre ese laboratorio es **sobre 45 puntos** (no se reparte Ser/Hacer dentro del producto).

La profesora, **fuera** del laboratorio, podrá **contrastar** el informe MONTI con Ser y Hacer. Eso no cambia el puntaje que MONTI emite para la casilla del laboratorio.

---

## 2. Rúbrica del laboratorio (total 45)

| Criterio | Máximo | Qué se valora | Fuente principal de evidencia |
|----------|--------|---------------|-------------------------------|
| **Procedimiento** | 18 | Cómo configura, mide, explora y ordena el intento en PhET | Telemetría de acciones + secuencia de eventos |
| **Comprensión** | 14 | Justificación y respuestas a preguntas socráticas de MONTI | Texto confirmado + diálogo tutor–estudiante |
| **Resultado físico** | 9 | Si el lanzamiento cumple objetivo dentro de tolerancia | Cálculo **servidor** (independiente del cliente) |
| **Evidencia de aprendizaje** | 4 | Progreso, uso del lab, constancia e historial de intentos (incluye `E(n)`) | Servidor + telemetría + diálogo |

**Convenciones físicas**: SI; `g = 10 m/s²`; sin resistencia del aire; tolerancia de objetivo **±0,5 m**.

**Política de intentos (`1.0`)**: exploración libre de penalización; en evaluación,  
`E(n) = max(0, 4 − 0,25 n(n + 1))` alimenta **Evidencia de aprendizaje** (máx. 4).  
`n` = fallos o reinicios **pedagógicos** computables (no técnicos).

---

## 3. Descriptores 0 % / 50 % / 100 %

### Procedimiento ( /18 )

| Banda | Puntos | Descriptor |
|-------|--------|------------|
| 0 % | 0 | No hay evidencia de un ciclo de intento usable (sin lanzamiento finalizado válido en la evidencia de evaluación). |
| 50 % | 9 | Hay lanzamiento y aterrizaje registrados, pero poca o nula exploración de controles/mediciones antes de entregar. |
| 100 % | 18 | Hay lanzamiento y aterrizaje **y** evidencia de ajuste de controles y/o mediciones que muestran un procedimiento intencional. |

### Comprensión ( /14 )

| Banda | Puntos | Descriptor |
|-------|--------|------------|
| 0 % | 0 | Sin explicación confirmada, o texto que no aborda la relación causa–efecto del alcance. |
| 50 % | 7 | Explicación presente pero incompleta (poca precisión conceptual o sin vincular variables al alcance). |
| 100 % | 14 | Explicación que relaciona de forma coherente variables (p. ej. ángulo, rapidez, componentes, gravedad) con el alcance u objetivo. |

### Resultado físico ( /9 )

| Banda | Puntos | Descriptor |
|-------|--------|------------|
| 0 % | 0 | El lanzamiento entregado queda fuera de la tolerancia ±0,5 m respecto al objetivo. |
| 50 % | — | No aplica banda intermedia: el verificador es binario (cumple / no cumple). |
| 100 % | 9 | El lanzamiento entregado cumple el objetivo dentro de ±0,5 m (`g = 10 m/s²`, sin aire). |

### Evidencia de aprendizaje ( /4 )

| Banda | Puntos | Descriptor |
|-------|--------|------------|
| 0 % | 0 | Historial con muchos fallos/reinicios pedagógicos: `E(n)` llega a 0. |
| 50 % | ~2 | Penalizaciones intermedias según `E(n)` (p. ej. n=2 → 2,5). |
| 100 % | 4 | Sin fallos pedagógicos computables en evaluación (`n = 0` → `E(0) = 4`), o solo fallos técnicos exentos. |

---

## 4. Ejemplos de explicación (Comprensión)

**Aceptable (orientado a 100 %):**  
«Mantuve la rapidez y subí el ángulo hacia 45° porque, sin resistencia del aire y con g = 10, el alcance horizontal depende de la componente horizontal y del tiempo de vuelo; cerca de 45° maximizo el alcance para llegar a la marca.»

**Rechazable (orientado a 0 %):**  
«Lo moví hasta que pegó» / «Porque sí» / texto vacío de justificación física.

---

## 5. Telemetría mínima PhET (kinds)

MONTI MUST poder registrar y mostrar:

| kind | Uso |
|------|-----|
| `control` | Cambio de control/parámetro |
| `launch` | Lanzamiento |
| `landed` | Aterrizaje / alcance observado |
| `measurement` | Medición |
| `pause` | Pausa |
| `erase` | Borrado |
| `reset` | Reinicio |
| `invalidated` | Invalidación (puede marcar fallo técnico) |

---

## 6. Fallos técnicos vs pedagógicos

| Tipo | Ejemplos | Efecto en `n` / `E(n)` |
|------|----------|-------------------------|
| **Técnico** | Simulación no lista / puente caído; pérdida de sesión no imputable al estudiante; invalidación marcada `technical_failure` | **NO** incrementa `n` |
| **Pedagógico** | Entrega fallida fuera de tolerancia; reinicio/borrado de un lanzamiento de evaluación sin entregar | **Sí** cuenta según política `1.0` |

---

## 7. Rol de MONTI y uso docente

1. Observación continua de telemetría PhET + diálogo (texto confirmado).  
2. Al cerrar evaluación, **emite** los cuatro puntajes con evidencia inspectable (reglas no generativas + física de servidor).  
3. **Informe detallado por alumno** (subpuntajes, total /45, evidencia) para cargar a registros.  
4. Flujo previsto: la profesora **carga el puntaje MONTI**; **no** hay override obligatorio en producto.  
5. Contraste con Ser/Hacer: **fuera** del laboratorio.

---

## 8. Entregables de cierre (`004`)

- [x] Descriptores 0 / 50 / 100 %  
- [x] Ejemplos de explicación aceptable / rechazable  
- [x] Fallos técnicos  
- [x] Telemetría mínima  
- [x] Versiones `45-v1` / política `1.0`  
- [x] Modelo carga docente (sin override obligatorio)  

Enmienda Constitución / README / alcance / código: tareas Speckit US2–US3.

---

## 9. Relación con el repo

| Documento | Relación |
|-----------|----------|
| `docs/alcance-mvp.md` | Alcance MVP; cita esta acta |
| `.specify/memory/constitution.md` | Enmienda alineada a §2–§7 |
| `specs/004-validacion-docente-rubrica-y-politica/` | Feature de cierre |
| LabSpec | `rubric_version: 45-v1`, `learning_evidence: 4` |

---

## 10. Registro de acuerdo

| Tema | Confirmación |
|------|----------------|
| Puntajes 18 / 14 / 9 / 4 | Sí (2026-10-26) |
| Criterios Procedimiento, Comprensión, Resultado físico, Evidencia de aprendizaje | Sí |
| Lab = casilla Saber; devolutiva /45 | Sí |
| MONTI observa telemetría + diálogo y puntúa los 4 | Sí |
| Informe detallado por alumno | Sí |
| Profesora carga el puntaje MONTI; Ser/Hacer fuera | Sí |
| Cierre formal versiones `45-v1` / `1.0` | Sí (2026-10-26) |
