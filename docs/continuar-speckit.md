# Continuar con Speckit — guía operativa

**Actualizado**: 2026-11-05  
**Estado**: auth local + alcance + cierre visual + rúbrica `45-v1` + **login Google Workspace (`005`)** hechos. Residual: OAuth real en navegador (runbook). No reabrir rúbrica ni `001` salvo bugs.

## Mapa rápido (canónico → carpeta en este repo)

| Ítem en `secuencia-features-speckit.md` | Carpeta Speckit | Estado |
|---|---|---|
| (slice local de) `004-supabase-auth-…` | `specs/001-school-auth-roles/` | Hecho (SQLite) |
| `001-alcance-mvp-y-reconciliacion-perfil` | `specs/002-alcance-mvp-y-reconciliacion-perfil/` + [`docs/alcance-mvp.md`](./alcance-mvp.md) | **Hecho** |
| `002-cierre-integracion-tecnica-visual` | `specs/003-cierre-integracion-tecnica-visual/` | **Hecho** — ver `docs/validacion.md` |
| `003-validacion-docente-rubrica-y-politica` | `specs/004-validacion-docente-rubrica-y-politica/` | **Hecho** — acta + `45-v1` / política `1.0` |
| IdP Google Workspace (parte de canónico `004`) | `specs/005-google-workspace-login/` | **Hecho** — runbook + `docs/validacion-google-005.md` |
| Resto Postgres/RLS aula | `specs/006-…` (cuando toque) | Pendiente |

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

### `005` login Google Workspace — cerrado (código + tests + runbook)

- Spec: `specs/005-google-workspace-login/`
- Runbook: [`docs/runbook-google-workspace.md`](./runbook-google-workspace.md)
- Evidencia: [`docs/validacion-google-005.md`](./validacion-google-005.md)
- Dominio `montessorisucre.edu.bo` · roster **sin** contraseñas · auth local `001` sigue para demos

**Siguiente:** merge del PR `005` si aún abierto, o siguiente feature (Postgres/RLS / modelo académico) cuando toque. No abrir RAG hasta identidad de aula usable en demo.

## Qué no abrir todavía

- Importar contraseñas del colegio  
- Corpus RAG / tutor LLM / voz generativa hasta haber probado OAuth real 1–2 cuentas  
- Concurrencia 30 / piloto formal completo  

## Comandos locales útiles

```bash
cd PG_AdaptaLab-2D/apps/api
source .venv/bin/activate
export MONTI_DATABASE_URL='sqlite:///./monti.sqlite3'
export MONTI_FEATURE_SCHOOL_AUTH=true
pytest -q
```

Arranque: `scripts/start-local.sh` o el flujo del README.
