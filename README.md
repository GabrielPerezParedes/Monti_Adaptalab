# MONTI 1.1.0 · Laboratorio de Física 2D

Base de implementación del proyecto de grado **Laboratorios Virtuales Web con Adaptabilidad basada en Agentes Inteligentes para Educación Secundaria**.

Primer tema: **movimiento parabólico, 4.º de secundaria, Colegio Montessori de Sucre**. Integra el código público de **PhET Projectile Motion** con preparación docente, registro de interacciones y verificación física independiente.

**Estado: primer hito técnico, para pruebas locales con datos de ejemplo.** El generador es paramétrico y MONTI presenta preguntas por reglas. Incluye un personaje provisional animado y movible, dictado y lectura de preguntas con la voz del navegador. Todavía no hay RAG, evaluación con un modelo de lenguaje, voz generativa ni autenticación escolar. La meta del piloto sigue siendo un curso de 30 estudiantes; esa concurrencia aún no está validada.

Lee `docs/version-1.1.0.md` para actualizar una instalación existente y probar el acceso y la voz.

## Qué puedes ejecutar

1. La profesora prepara una actividad con curso y dificultad, revisa objetivo y tolerancia, comparte el enlace y publica.
2. El estudiante ve una sala de espera hasta la publicación y entra con un alias de prueba.
3. La aplicación configura la pantalla Intro de PhET: ángulo, rapidez, altura, objetivo, gravedad y controles habilitados.
4. PhET emite ajustes, lanzamientos, aterrizajes, borrados, reinicios, mediciones y cambios de visualización. El navegador conserva una cola pendiente y el servidor evita duplicar eventos reenviados.
5. El estudiante explora, inicia evaluación, explica su razonamiento y entrega un lanzamiento finalizado.
6. El servidor calcula resultado físico y eficiencia. La profesora revisa procedimiento y comprensión con las acciones y explicaciones a la vista.
7. Ambos pueden descargar resúmenes de texto con condiciones, resultado y puntuación.

En esta versión se generan parámetros y se configura la escena existente de PhET. **No se generan nuevos componentes gráficos ni código de simulación mediante IA**. La integración completa descrita en el proyecto de grado se desarrolla en los siguientes hitos.

## Tecnologías

| Parte | Esta base | Siguiente integración prevista |
|---|---|---|
| Web | React 19, TypeScript, Vite | Diseño definitivo de MONTI y diálogo accesible |
| Servidor | Python 3.12, FastAPI, Pydantic | Orquestación de generación y evaluación |
| Simulación | PhET Projectile Motion, `adapted-from-phet` | Actividades validadas del tema acordado |
| Persistencia | SQLAlchemy y SQLite local | PostgreSQL, Supabase Auth y migraciones |
| Bibliografía | Referencias de RACSO y convenciones físicas | Ingesta revisada, fragmentos con página, pgvector |
| Tutor | Personaje animado, dictado, voz del navegador y preguntas por reglas | RAG, diálogo con IA, voz y animación |

SQLite permite empezar sin cuentas externas. La decisión de utilizar PostgreSQL/Supabase para el producto escolar se mantiene. La API permite configurar una conexión PostgreSQL; esa conexión no se ha probado en este hito.

## Instalación

Necesitas **Git**, **Node.js 22.12 o superior con npm** y **Python 3.12**. Se verificó la compilación con Node 24.19 y Python 3.12. La primera preparación de PhET descarga 22 repositorios públicos y sus dependencias; necesita conexión y espacio disponible.

### 1. Obtener el código e instalar la web

Si esta rama ya está disponible en GitHub:

```bash
git clone https://github.com/GabrielPerezParedes/PG_AdaptaLab-2D.git
cd PG_AdaptaLab-2D
git switch feat/monti-1.1.0
npm ci
```

Si recibiste un ZIP o un Git bundle, sigue `docs/entrega-del-codigo.md`. Si ya tienes esta copia, ejecuta solamente `npm ci` desde su raíz. La rama debe existir localmente o en GitHub antes de usar `git switch`.

### 2. Preparar PhET

Windows PowerShell, desde la raíz:

```powershell
py -3.12 scripts/setup_phet.py
```

Linux o macOS:

```bash
python3 scripts/setup_phet.py
```

El script descarga las revisiones exactas de `integrations/phet/sources.lock.json`, aplica la integración y compila el HTML en español en `apps/web/public/phet/projectile-motion.html`. Las fuentes descargadas quedan en `.phet/` y no se suben al repositorio. La preparación puede tardar varios minutos y se puede volver a ejecutar. `--fetch-only` descarga sin compilar.

El aviso de PhET sobre `build-local.json` es opcional para esta compilación pública. No necesitas credenciales internas de PhET. El compilador público omite por diseño su comprobación global de tipos porque incluye dependencias privadas de PhET-iO; sí transpila y empaqueta las dependencias públicas.

### 3. Iniciar la API — primera terminal

Windows PowerShell:

```powershell
cd apps/api
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
Copy-Item .env.example .env
.venv\Scripts\python.exe -m uvicorn monti.main:app --env-file .env --reload --host 127.0.0.1 --port 8000
```

Linux o macOS:

```bash
cd apps/api
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
cp .env.example .env
.venv/bin/python -m uvicorn monti.main:app --env-file .env --reload --host 127.0.0.1 --port 8000
```

La base `monti.sqlite3` se crea en `apps/api/`. No se requiere activar el entorno virtual. `requirements.lock` fija las versiones verificadas e incluye herramientas de prueba.

### 4. Iniciar la web — segunda terminal

Desde la raíz del repositorio:

```bash
npm run dev
```

Abre [el espacio docente local](http://localhost:5173/teacher). La web dirige `/api` al servidor del puerto 8000. Consulta [la documentación de la API](http://127.0.0.1:8000/docs) si necesitas inspeccionar sus contratos.

Usa dos pestañas para probar ambos roles. Prepara una actividad, copia su enlace y ábrelo antes de publicar para comprobar la espera. Publica desde la pestaña docente y entra como estudiante. Inicia evaluación **antes de realizar el lanzamiento que entregarás**.

La clave docente predeterminada es pública y solo identifica el flujo de desarrollo. Mantén datos de ejemplo. Los servidores están limitados al equipo local; el despliegue escolar requiere autenticación, HTTPS y una prueba de concurrencia.

## Evaluación sobre 45 puntos

| Criterio | Máximo | Implementación actual |
|---|---:|---|
| Procedimiento técnico | 18 | Revisión docente de las acciones |
| Comprensión y justificación | 14 | Revisión docente de las explicaciones |
| Resultado físico | 9 | Cálculo independiente del servidor |
| Eficiencia e intentos | 4 | Fallos y reinicios computables |

Un criterio sin revisar figura **pendiente**. El total aparece al valorar los cuatro criterios. Las revisiones se conservan: nueva evidencia deja la revisión anterior en el historial y requiere valorar la evidencia actual.

Convenciones: SI, `g = 10 m/s²`, sin resistencia del aire, llegada al suelo `y = 0`, tolerancia `±0,5 m`. El generador conserva una solución testigo en el servidor para garantizar un objetivo alcanzable.

Política provisional: exploración libre; en evaluación, una entrega fallida o el borrado/reinicio de un lanzamiento sin entregar cuenta una vez por lanzamiento. Un fallo ya entregado no vuelve a penalizarse al reiniciar. `E(n) = max(0, 4 − 0,25 n(n + 1))`: 4; 3,5; 2,5; 1; 0. La profesora debe validar esta política, las tolerancias y los indicadores pedagógicos.

## Organización

| Ruta | Contenido |
|---|---|
| `apps/web/src/App.tsx` | Páginas docente y estudiante |
| `apps/web/src/PhETLab.tsx` | Contenedor y comunicación con PhET |
| `apps/api/monti/main.py` | API, eventos, revisión y reportes |
| `apps/api/monti/generation.py` | Generación paramétrica reproducible |
| `apps/api/monti/physics.py` | Verificador físico y eficiencia |
| `apps/api/monti/schemas.py` | Contratos y validación |
| `apps/api/monti/database.py` | Persistencia de actividades y evidencias |
| `integrations/phet/` | Adaptador, fuentes fijadas, parches y pruebas |
| `scripts/setup_phet.py` | Preparación reproducible de PhET |
| `docs/` | Arquitectura, entrega, validación y siguientes hitos |

No subas dependencias instaladas, `.env`, bases de datos, compilaciones ni el PDF completo de la bibliografía. Las carpetas generadas están excluidas del control de versiones.

## Verificación

Desde la raíz:

```bash
npm run build
npm run test:bridge
```

Desde `apps/api`, Windows:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Desde `apps/api`, Linux o macOS:

```bash
.venv/bin/python -m pytest -q
```

Las pruebas cubren física de referencia, 300 configuraciones alcanzables, publicación, sesiones, reenvíos, rechazo de datos incompatibles, penalizaciones, reportes e historial. Las pruebas del puente utilizan propiedades controladas; no sustituyen la comprobación visual con PhET real. El alcance exacto está en `docs/validacion.md`.

## Fuentes

PhET Projectile Motion es una obra de **PhET Interactive Simulations, University of Colorado Boulder**. Se adapta su [código público](https://github.com/phetsims/projectile-motion) conservando la marca `adapted-from-phet`. No es un producto oficial de PhET y no utiliza PhET-iO. Su fuente tiene [licencia GPL v3](https://github.com/phetsims/projectile-motion/blob/main/LICENSE). Consulta `THIRD_PARTY_NOTICES.md` antes de distribuir una compilación.

Referencia pedagógica: *Problemas de física y cómo resolverlos*, RACSO, edición 2009, dirección de Félix Aucallanchi Velásquez, capítulo 8. Se distinguen páginas impresas y páginas PDF. El libro completo no forma parte del repositorio; su ingesta revisada en el RAG es un hito posterior.
