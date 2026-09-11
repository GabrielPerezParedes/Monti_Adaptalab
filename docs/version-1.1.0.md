# Versión 1.1.0 — acceso y personaje MONTI

## Cambios

- La página docente muestra el código de actividad junto al enlace, con acciones separadas para copiarlos.
- Un enlace válido abre directamente la espera o el formulario de ingreso. El código se introduce únicamente si se entra sin enlace; se puede cambiar de actividad.
- MONTI es un personaje provisional de robot, animado y flotante sobre el laboratorio. Se mueve arrastrándolo o con las flechas cuando tiene el foco. Se puede minimizar su globo de conversación.
- «Hablar una vez» activa el dictado de una intervención. «Escucha continua» permite seguir dictando hasta apagarla. El texto se revisa y guarda como explicación mediante el servidor existente.
- «Escuchar a MONTI» lee la pregunta actual en voz alta. El personaje cambia de estado al escuchar y hablar.
- La escucha se pausa mientras MONTI habla, se retoma si estaba en modo continuo y se detiene al ocultar o abandonar la página. Un permiso denegado detiene los reintentos.

El robot utiliza el emoji nativo 🤖 como recurso provisional; su apariencia depende del sistema. El movimiento respeta la preferencia de reducir animaciones.

## Actualizar tu instalación

1. Guarda una copia de tus modificaciones propias. Incorpora los archivos del ZIP o la rama `feat/monti-1.1.0` del bundle.
2. Conserva `.env`, `apps/api/monti.sqlite3`, `.venv`, `node_modules`, `.phet` y `apps/web/public/phet`. El ZIP no contiene esas carpetas y archivos locales. Esta actualización no cambia el esquema de la base ni el adaptador de PhET; no necesitas recompilar PhET.
3. Reinicia la API y la web con los comandos del README. Si es una instalación nueva, sigue su preparación completa.
4. Prepara una actividad, copia el enlace y comprueba que permite ingresar sin volver a buscar el código. Prueba también entrar por código desde `/student`.
5. En el laboratorio, mueve el robot, prueba dictado, escucha continua y lectura de la pregunta. Habilita el micrófono cuando lo solicite el navegador. Comprueba que el indicador se apaga al detenerlo.

## Alcance de la voz

Usa [SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) y [SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis), con detección de disponibilidad. El reconocimiento tiene compatibilidad limitada y puede utilizar un servicio externo del navegador; no se garantiza funcionamiento sin conexión. Usa localhost o HTTPS. La página conserva la alternativa escrita cuando el dictado no está disponible.

Es voz del navegador, no voz generativa de un modelo de IA. MONTI sigue presentando las preguntas de la guía por reglas: todavía no responde libremente dudas mediante RAG. Esta versión no exige claves de API ni nuevas dependencias. MONTI no guarda archivos de audio en su servidor; guarda el texto cuando el estudiante pulsa «Guardar explicación».

## Verificación y siguiente paso

Se comprueban compilación y tipos, y tres pruebas controladas del ciclo de voz: activación explícita y duplicados, reanudación y permisos, pausa durante lectura y limpieza al salir. No sustituyen la validación con micrófono y altavoces en tu navegador.

La Constitución y las especificaciones SDD se redactarán en la siguiente sesión. Este registro documenta el cambio implementado; no establece principios nuevos para el proyecto ni sustituye esas especificaciones.
