# Arquitectura inicial

## Responsabilidades

React reúne las páginas docente y estudiante. FastAPI conserva actividades, intentos y evidencias. PhET ejecuta la simulación en un iframe del mismo origen que React. El adaptador añadido a su fuente observa el modelo real y comunica eventos mediante `postMessage`.

La interfaz comprueba origen, ventana emisora, versión y canal. El canal separa instancias; no es una credencial. La API valida esquema, pertenencia a la sesión, condiciones del lanzamiento y publicación. Calcula la trayectoria con sus propias ecuaciones y no acepta notas enviadas por el navegador.

Un navegador modificado aún puede fabricar evidencia compatible con esas reglas. La base no garantiza autenticidad de un cliente manipulado. Con `MONTI_FEATURE_SCHOOL_AUTH=true`, la API usa autenticación de primer partido (usuarios/roles/sesiones opacas en SQLAlchemy), alcance por asignatura/matrícula y retira `X-Teacher-Key` del flujo de aula. Con el flag en falso se conserva el prototipo local (clave docente pública + alias). El despliegue escolar requiere HTTPS.

## Actividad generada

La solicitud contiene curso, dificultad y semilla. El generador construye un lanzamiento válido, calcula su alcance y prepara un objetivo redondeado. Separa la solución testigo privada de la consigna pública. La semilla hace reproducible la actividad; esta versión no pretende ocultar la solución frente a quien inspeccione el código del generador.

En dificultad básica se fijan rapidez y altura. En media se permite modificar rapidez y ángulo. En avanzada se añade una altura inicial positiva fija. Todas las variantes declaran gravedad y ausencia de resistencia del aire.

Antes de publicar, la consulta del estudiante devuelve `published: false` y `spec: null`; no permite incorporarse. Después, todos los estudiantes reciben la misma especificación. Las variantes individuales se añadirán tras validar equivalencia de dificultad.

Esta primera generación configura una escena ya implementada de PhET. No crea gráficos ni controles arbitrarios. El siguiente generador con RAG producirá especificaciones estructuradas dentro de las capacidades que admita el adaptador.

## Eventos

| Evento | Evidencia |
|---|---|
| `control` | Variable o visualización y su valor; cambios rápidos agrupados |
| `launch` | Identificador y condiciones iniciales en SI |
| `landed` | Alcance y tiempo observados al llegar al suelo |
| `measurement` | Lectura de la sonda |
| `pause` | Pausa o continuación |
| `erase`, `reset` | Borrado o reinicio |
| `invalidated` | Cambio incompatible durante el lanzamiento |

Cada evento tiene UUID. El navegador conserva pendientes en almacenamiento local y envía lotes ordenados de hasta 100. Un lote rechazado se revierte completo. Reenviar el mismo evento no crea otro registro; cambiar el contenido de un ID existente se rechaza.

La cola cubre reintentos de envío; no garantiza uso indefinido sin conexión. No se restaura la escena completa de PhET al recargar: los registros permanecen, pero la interfaz necesita un nuevo lanzamiento para entregar.

El adaptador limita a un proyectil en vuelo. Reiniciar conserva objetivo, gravedad y condiciones asignadas. Desactiva el control de rapidez cuando está fijada y el movimiento del objetivo. Una modificación de altura fijada se restaura mediante una actualización diferida de la propiedad. Se conservan medición y vectores.

Exploración y evaluación son fases distintas. Solo se entrega un lanzamiento creado durante evaluación, finalizado, válido y sin abandonar. Las observaciones se contrastan con la física del servidor cuando se reciben. Las preguntas actuales dependen del número de lanzamientos; no interpretan el razonamiento con IA.

## Física y revisión

Para rapidez `v`, ángulo `θ`, altura `h` y gravedad `g`:

- `vx = v cos θ`; `vy = v sin θ`.
- `t = (vy + sqrt(vy² + 2gh)) / g`.
- `alcance = vx t`.
- `altura máxima = h + vy² / (2g)`, para los ángulos positivos admitidos.

La tolerancia del objetivo es 0,5 m. La comprobación adicional del alcance observado admite 0,05 m frente al verificador. Son reglas diferentes.

Cada revisión docente conserva fundamento, fecha, entrega, número de eventos y número de explicaciones considerados. Nueva evidencia no borra revisiones: vuelve pendiente el total actual. El resumen incluye condiciones, alcance, tiempo, altura máxima, nota y última explicación. Es un resumen determinista, no una interpretación generativa del razonamiento.

## Próxima integración de IA

El RAG recuperará fragmentos con identificador y página verificados del capítulo elegido. El generador propondrá una especificación; el servidor comprobará intervalos, coherencia y existencia de solución antes de publicarla. No se ejecutará como código arbitrario una respuesta del modelo.

MONTI recibirá actividad, historial resumido, explicaciones y fragmentos pertinentes. Pedirá predicciones y justificaciones y propondrá valoraciones ligadas a indicadores y evidencias. La profesora podrá revisarlas. Estas responsabilidades están previstas, todavía no implementadas.

Claves de IA y conexión al corpus permanecerán en el servidor. Personaje, audio y captura de voz se incorporarán después de validar el diálogo escrito y su evaluación.

## Actualización 1.1.0

Se añade el personaje flotante y una capa de voz del navegador (`voice.ts`), separada de la evaluación. El dictado alimenta la explicación editable; no envía audio al servidor de MONTI. La voz generativa y el diálogo mediante RAG permanecen pendientes. El alcance y la actualización se describen en `version-1.1.0.md`.
