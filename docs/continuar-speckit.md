# Continuar con Speckit — guía operativa

**Actualizado**: 2026-10-26  
**Estado**: auth local + alcance MVP + cierre visual + **rúbrica `45-v1`** (`specs/004-…`, `docs/acta-rubrica-profesora.md`) **hechos**. Siguiente: identidad de producción / resto Oleada B (no reabrir rúbrica salvo enmienda).

## Mapa rápido (canónico → carpeta en este repo)

| Ítem en `secuencia-features-speckit.md` | Carpeta Speckit | Estado |
|---|---|---|
| (slice local de) `004-supabase-auth-…` | `specs/001-school-auth-roles/` | Hecho (SQLite) |
| `001-alcance-mvp-y-reconciliacion-perfil` | `specs/002-alcance-mvp-y-reconciliacion-perfil/` + [`docs/alcance-mvp.md`](./alcance-mvp.md) | **Hecho** |
| `002-cierre-integracion-tecnica-visual` | `specs/003-cierre-integracion-tecnica-visual/` | **Hecho** — ver `docs/validacion.md` |
| `003-validacion-docente-rubrica-y-politica` | `specs/004-validacion-docente-rubrica-y-politica/` | **Hecho** — acta + `45-v1` / política `1.0` |
| Resto de `004` (Supabase/Postgres/RLS) | `specs/005-…` (cuando toque) | Pendiente |

## Flujo por feature (copiar en el chat de Cursor)

Orden fijo:

1. `/speckit-specify` + descripción de la feature  
2. `/speckit-clarify` (solo si quedan huecos que bloqueen el plan)  
3. `/speckit-plan`  
4. `/speckit-tasks`  
5. `/speckit-analyze` (opcional si hay dudas)  
6. `/speckit-implement`  
7. `/speckit-checklist` (útil en cierre visual y rúbrica)  
8. Skill `nueva-rama` cuando el incremento esté listo para PR

### `002` alcance — cerrado

Doc canónico: [`docs/alcance-mvp.md`](./alcance-mvp.md).

### `003` cierre visual — cerrado

Evidencia: [`docs/validacion.md`](./validacion.md).

### `004` rúbrica docente — cerrado

Acta: [`docs/acta-rubrica-profesora.md`](./acta-rubrica-profesora.md). Versiones producto: `rubric_version=45-v1`, `attempt_policy.version=1.0`, criterio `learning_evidence`.

## Qué no abrir todavía

- Corpus RAG, tutor LLM, voz generativa (`006+` canónico)  
- Concurrencia 30 / piloto formal hasta identidad de producción  

## Comandos locales útiles

```bash
cd PG_AdaptaLab-2D/apps/api
source .venv/bin/activate
export MONTI_DATABASE_URL='sqlite:///./monti.sqlite3'
export MONTI_FEATURE_SCHOOL_AUTH=true
pytest -q
```

Arranque: `scripts/start-local.sh` o el flujo del README.
