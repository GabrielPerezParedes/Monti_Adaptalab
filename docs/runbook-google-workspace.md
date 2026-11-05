# Runbook — Login Google Workspace (Colegio Montessori de Sucre)

**Feature**: `specs/005-google-workspace-login/`  
**Dominio permitido**: `montessorisucre.edu.bo`  
**Principio**: MONTI **no almacena contraseñas** del colegio. Google autentica; el **roster** autoriza el aula.

## Resultado esperado

Tras este runbook puedes probar **1 docente + 1 estudiante** institucionales con “Continuar con Google” y obtener sesión Bearer MONTI.

## Prerrequisitos

- Cuenta **Administrador** Google Workspace del colegio (o OAuth client ya creado)
- Proyecto **Supabase** (Auth + JWT secret)
- API/web locales o de piloto con flags:
  - `MONTI_FEATURE_SCHOOL_AUTH=true`
  - `MONTI_FEATURE_GOOGLE_LOGIN=true`
  - `MONTI_GOOGLE_ALLOWED_DOMAIN=montessorisucre.edu.bo`
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
- **No** uses `MONTI_DEV_TEACHER_KEY` para el camino de aula Google; la clave docente es solo demos locales sin IdP

## 1. Google Cloud — OAuth client

1. Consola Google Cloud → APIs y servicios → Credenciales → **Crear cliente OAuth** (tipo *Aplicación web*).
2. Pantalla de consentimiento: uso **interno** / prueba con cuentas del dominio del colegio.
3. Redirect URIs típicos (ajustar a tu entorno):
   - `http://localhost:5173` (Vite / callback manejado por Supabase o la app)
   - `http://127.0.0.1:5173`
   - Redirect de Supabase: `https://<PROJECT_REF>.supabase.co/auth/v1/callback`
   - URI del entorno de piloto cuando exista (HTTPS)
4. Guarda Client ID y Client Secret **solo** en el dashboard de Supabase / secretos locales. **Nunca** en git.

## 2. Supabase Auth → proveedor Google

1. Supabase → Authentication → Providers → **Google** → activar.
2. Pegar Client ID / Secret del paso anterior.
3. Confirmar redirect URI de Supabase en Google Cloud.
4. Authentication → URL configuration: Site URL = origen de la web (localhost o piloto).
5. Copiar **JWT Secret** del proyecto → `SUPABASE_JWT_SECRET` en `apps/api/.env` (y análogo en web: URL + anon key).

## 3. Restricción de dominio

- En MONTI: `MONTI_GOOGLE_ALLOWED_DOMAIN=montessorisucre.edu.bo` (rechazo 403 fuera de dominio).
- En Google / Workspace: preferir cuentas del dominio institucional; opcional `hd` en el flujo OAuth.
- Health debe exponer `google_login: true` solo si flag + JWT secret están presentes.

## 4. Roster (sin contraseñas)

Antes del primer login Google de cada persona:

1. Entrar como admin local (seed `001`) o ya Google-admin.
2. Admin → roster: alta por formulario o CSV con columnas permitidas (`email`, `role`, `display_name`, `grade_id`, `subject_id`, `active`).
3. Cualquier columna con `password` / `passwd` / `clave` / `secret` / `token` → **rechazo**.
4. Sembrar al menos:
   - 1× `teacher@…@montessorisucre.edu.bo` role `teacher`
   - 1× estudiante del dominio role `student` + `grade_id` / `subject_id`

## 5. Checklist “listo para 1–2 cuentas”

- [ ] OAuth client + redirect URIs (localhost + Supabase callback)
- [ ] Supabase Google provider ON; JWT secret en API
- [ ] `GET /api/health` → `google_login: true`, dominio correcto
- [ ] Roster con ≥1 teacher y ≥1 student activos
- [ ] Login Google → Bearer MONTI; logout invalida sesión
- [ ] `@gmail.com` / email fuera de dominio → sin sesión de aula
- [ ] Email del dominio **sin** fila roster → mensaje de no estar en el piloto
- [ ] Confirmado: **MONTI no guarda contraseñas del colegio**

## 6. Flags y demos locales

| Camino | Flags | Uso |
|--------|-------|-----|
| Aula Google | `GOOGLE_LOGIN=true` + JWT + roster | Piloto / demo institucional |
| Demo local `001` | `SCHOOL_AUTH=true`, Google off | Sin depender de Workspace |
| Clave docente | `MONTI_DEV_TEACHER_KEY` | Solo desarrollo; **no** requerida si el aula usa Google |

## 7. Evidencia

Registrar resultado en [`validacion-google-005.md`](./validacion-google-005.md) (emails de prueba, sin secretos).
