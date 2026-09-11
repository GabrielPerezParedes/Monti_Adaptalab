# Verificación del primer hito

Entorno: Node.js 24.19.0, npm 11.9.0, Python 3.12.13, Linux. Fuentes PhET y dependencias están fijadas por revisión o versión.

| Verificación | Resultado |
|---|---|
| React y TypeScript | Compilación comprobada |
| API y dominio | 9 pruebas aprobadas, incluyen 300 configuraciones alcanzables |
| Protocolo del adaptador | 4 pruebas aprobadas con propiedades controladas |
| PhET real | Transpilación, empaquetado y HTML adaptado en español completados |
| Recorrido visual completo | Pendiente |
| PostgreSQL/Supabase | Pendiente |
| 30 usuarios concurrentes | Pendiente |
| Windows y macOS | Instrucciones incluidas, no ejecutadas en esos sistemas |

Las pruebas del adaptador no sustituyen una prueba en navegador con la compilación real. El compilador público de PhET omite por diseño su chequeo global de tipos al no disponer de dependencias privadas de PhET-iO. La comprobación de tipos de React sí se ejecuta.

## Recorrido manual pendiente

1. Preparar un laboratorio y abrir su enlace antes de publicar; comprobar espera y salida al publicar.
2. Entrar con alias, comprobar condiciones y objetivo en PhET y probar los tres niveles.
3. Cambiar variables, vectores y mediciones; comprobar acciones en la página docente.
4. Explorar, iniciar evaluación y hacer un lanzamiento nuevo. Entregar un fallo y reenviarlo; comprobar una penalización.
5. Reiniciar y verificar objetivo y gravedad. Alcanzar el objetivo y entregar una explicación.
6. Revisar desde la página docente y descargar ambos resúmenes.
7. Añadir una explicación y comprobar que se conserva el historial y vuelve pendiente la valoración actual.

Todavía no hay resultados pedagógicos medidos. Se obtendrán en el piloto acordado con el colegio, después de integrar autenticación escolar y validar el recorrido.
