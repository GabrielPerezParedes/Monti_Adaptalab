# Validación quickstart — `001-school-auth-roles`

**Fecha**: 2026-09-18  
**Entorno**: macOS, SQLite local (`apps/api/monti.sqlite3`), flags `MONTI_FEATURE_SCHOOL_AUTH` / `VITE_FEATURE_SCHOOL_AUTH`  
**Tarea Speckit**: T050

## Resumen

| Escenario | Resultado | Notas |
|---|---|---|
| A — Bootstrap admin | **PASS** | Seed idempotente; login admin → token + `role: admin` |
| B — Catálogo / provisión | **PASS** (UI) | Admin crea grados, asignaturas, usuarios, asignaciones y matrículas |
| C — Alcance profesor | **PASS** (API tests) | `test_teacher_scope.py`; admin puede entrar a `/teacher` |
| D — Alcance alumno | **PASS** (API tests) | `test_student_enrollment.py` |
| E — Lockout / sesión | **PASS** (API tests) | `test_login_throttle.py`; logout/me |
| F — UI humo | **PASS** parcial | Login → admin OK; `/teacher` tras migración de `labs` OK (antes 500 por `grade_id`) |
| Regresión pytest | **PASS** | `18 passed` (2026-09-18) con `MONTI_DATABASE_URL=sqlite://…` |

## Incidente resuelto (schema)

Tras implementar la feature, `GET /api/teacher/labs` devolvía 500: la tabla `labs` no tenía `grade_id` / `subject_id` porque `create_all` no altera tablas existentes y Alembic no se había aplicado (y `alembic upgrade` chocaba con tablas auth ya creadas).

**Remedio aplicado**: columnas añadidas en SQLite + `alembic_version = e048039af4bc`.

## Comandos de verificación

```bash
cd PG_AdaptaLab-2D/apps/api
source .venv/bin/activate
MONTI_DATABASE_URL='sqlite:///./monti.sqlite3' pytest -q
```

Migración en entorno **ya parcialmente creado** por `create_all`: no usar solo `alembic upgrade head` (falla con *table already exists*). Preferir stamp + columnas (ver quickstart) o base limpia.

## Pendiente fuera de esta feature

- Alcance MVP reconciliado → siguiente Speckit: `002-alcance-mvp-y-reconciliacion-perfil`
- Recorrido PhET completo → `docs/validacion.md` / luego `003-cierre-integracion-tecnica-visual`
- Rúbrica no-`draft` → puerta docente (`004-validacion-docente-rubrica-y-politica`)
- Postgres / Supabase Auth / RLS → resto de Oleada B (ítem canónico `004-supabase-…` en la secuencia)
