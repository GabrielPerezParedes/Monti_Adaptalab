# Validación — Login Google Workspace (`005`)

**Fecha**: 2026-11-04  
**Feature**: `specs/005-google-workspace-login/`  
**Entorno**: API local (SQLite) + pytest; OAuth real = dry-run documentado (runbook listo, sin secretos en repo)

## Escenarios quickstart

| Escenario | Resultado | Notas |
|-----------|-----------|-------|
| A. Runbook | **Pass (doc)** | `docs/runbook-google-workspace.md` cubre OAuth client, Supabase Google, dominio, roster, checklist 1–2 cuentas |
| B. Login feliz | **Pass (automatizado)** | `test_google_login_issues_monti_session` — token mock + roster → Bearer MONTI, `auth_provider=google` |
| C. Rechazos | **Pass (automatizado)** | Dominio inválido (`@gmail.com`); sin fila roster; health expone `google_login` + dominio |
| D. Roster | **Pass (automatizado)** | CSV con `password` → 422; import OK; cambio de `role` se refleja en siguiente login |
| E. Regresión local | **Pass (automatizado)** | `tests/test_auth_session.py` con school auth; Google no rompe login local |
| F. OAuth real en navegador | **Pendiente / dry-run** | Requiere Client ID/Secret + cuentas `@montessorisucre.edu.bo` en Workspace; seguir runbook fuera del CI |

## Cuentas de prueba (sin secretos)

| Email (ejemplo) | Rol roster | Uso |
|-----------------|------------|-----|
| `alumno@montessorisucre.edu.bo` | student | Happy path pytest |
| `docente@montessorisucre.edu.bo` | teacher → admin | Import CSV + cambio de rol |
| `admin@monti.local` | admin local | Seed `001` para APIs de roster |

## Residuales

- Completar OAuth end-to-end en navegador cuando el autor configure el client Workspace + Supabase.
- Postgres/RLS de producción siguen fuera de `005` (canónico restante).
- `MONTI_DEV_TEACHER_KEY` no es requerida para el camino Google documentado en el runbook.

## Conclusión

Implementación `005` **cerrada a nivel código + tests + runbook**. Evidencia de UI OAuth real queda como residual operativo del autor (no bloquea mark Implemented del Speckit).
