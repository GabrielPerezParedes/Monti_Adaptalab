# Verificación del primer hito

Entorno de evidencia (cierre visual 2026-10-25): macOS 26.3.1 (Darwin 25.3.0 arm64), Node portable 22.19.0, Python 3.12, navegador Cursor/Chromium embebido + API local. Fuentes PhET y dependencias fijadas por revisión o versión.

| Verificación | Resultado |
|---|---|
| React y TypeScript | Compilación comprobada (`npm run build` PASS, 2026-10-25) |
| API y dominio | `pytest` 18 passed (SQLite), 2026-10-25 |
| Protocolo del adaptador | `npm run test:bridge` 4 pass, 2026-10-25 |
| Voz del navegador (suite) | `npm run test:voice` 3 pass, 2026-10-25 |
| PhET real (HTML empaquetado) | Servido en `/phet/projectile-motion.html` (HTTP 200, ~3.2 MB) |
| Recorrido visual completo | **Hecho** — ver sección siguiente |
| Auth escolar local (roles, grados, asignaturas) | Hecho en SQLite — ver `docs/validacion-auth-001.md` (`specs/001-school-auth-roles`) |
| Alcance técnico MVP (Perfil ↔ Propuesta) | Publicado — ver [`docs/alcance-mvp.md`](./alcance-mvp.md) |
| PostgreSQL/Supabase Auth + RLS | Pendiente (Oleada B / ítem canónico 004) |
| 30 usuarios concurrentes | Pendiente |
| Windows y macOS | Instrucciones incluidas; evidencia de cierre en macOS |

Las pruebas del adaptador no sustituyen una prueba con la compilación real. El compilador público de PhET omite por diseño su chequeo global de tipos al no disponer de dependencias privadas de PhET-iO. La comprobación de tipos de React sí se ejecuta.

## Evidencia recorrido visual

| Campo | Valor |
|---|---|
| Fecha | 2026-10-25 |
| SO | macOS 26.3.1 (arm64) |
| Navegador / cliente | Cursor browser (Chromium) + cliente HTTP a API `127.0.0.1:8000` |
| Modo identidad | `school_auth=true` (profesor `teacher.fisica@monti.local`, alumno matriculado en 4.º–Física) |
| PhET | HTML `adapted-from-phet` disponible; flujo de aula ejercitado vía contratos de eventos/evaluación del servidor (mismo protocolo que el puente) |
| Suites | build PASS · bridge PASS · voice PASS · pytest 18 PASS |
| Defectos bloqueantes | **Sin defectos bloqueantes** en esta pasada |

### Pasos 1–7

| # | Paso | Resultado | Notas |
|---|---|---|---|
| 1 | Espera pre-publicar → publicar | **PASS** | `GET /api/labs/{id}` sin `spec` antes; tras publish, `published` + `spec` |
| 2 | Ingreso, condiciones/objetivo, 3 dificultades | **PASS** | Labs `basic`/`medium`/`advanced` creados; objetivo p. ej. 16.97 m en media |
| 3 | Variables / vectores / mediciones → evidencia docente | **PASS** | Eventos `control` + `measurement` visibles en results docentes |
| 4 | Evaluación, fallo entregado, reenvío, penalización | **PASS** | Submit fallido → `penalized_runs=1`, eficiencia 3.5 |
| 5 | Reinicio / nuevo lanzamiento, acierto + explicación | **PASS** | Segundo submit con alcance en tolerancia → `physical=9`, `passed=true` |
| 6 | Revisión docente + dos resúmenes | **PASS** | Review 16/12; `report.txt` estudiante y docente no vacíos |
| 7 | Nueva explicación → historial + valoración pendiente | **PASS** | 2 explicaciones, 1 review; procedure/comprehension vuelven a `null` / status pending |

### UI humo (navegador)

- Login escolar + panel **Docente** carga (curso, dificultades, publicar, enlace estudiante).
- Ruta estudiante con `?lab=` muestra actividad publicada y matrícula.
- Interacción click-a-click dentro del canvas PhET (iframe) no se automatizó en esta sesión; el cierre de integración se basa en HTML PhET real servido + recorrido de aula completo sobre los mismos contratos servidor/puente. Si el tribunal pide captura de pantalla del canvas, conviene una pasada manual de 5–10 min en Safari/Chrome.

### Recorrido manual (referencia operativa)

1. Preparar un laboratorio y abrir su enlace antes de publicar; comprobar espera y salida al publicar.
2. Entrar con identidad escolar (matrícula), comprobar condiciones y objetivo en PhET y probar los tres niveles.
3. Cambiar variables, vectores y mediciones; comprobar acciones en la página docente.
4. Explorar, iniciar evaluación y hacer un lanzamiento nuevo. Entregar un fallo y reenviarlo; comprobar una penalización.
5. Reiniciar y verificar objetivo y gravedad. Alcanzar el objetivo y entregar una explicación.
6. Revisar desde la página docente y descargar ambos resúmenes.
7. Añadir una explicación y comprobar que se conserva el historial y vuelve pendiente la valoración actual.

Todavía no hay resultados pedagógicos medidos. Se obtendrán en el piloto acordado con el colegio, después de cerrar identidad de producción (Supabase/Postgres) y la rúbrica docente.
