# Componentes de terceros

## PhET Projectile Motion

Autores: PhET Interactive Simulations, University of Colorado Boulder. [Código original](https://github.com/phetsims/projectile-motion).

El simulador conserva GPL v3, copyright y atribuciones de medios incorporadas por el compilador. La licencia se copia en `integrations/phet/LICENSE-PhET.txt`. Se utiliza la marca `adapted-from-phet`; no se presenta como una versión oficial ni se utiliza PhET-iO.

`integrations/phet/installMontiBridge.js` se aporta bajo GPL-3.0-or-later para integrarlo con el simulador. Los parches añaden observación y configuración en dos vistas, conservando el motor físico. Las revisiones originales están en `integrations/phet/sources.lock.json`.

## Herramientas de PhET

Cada biblioteca descargada conserva su licencia. Los cambios de compatibilidad en Chipper sustituyen metadatos que presuponen el monorepositorio `totality` por los commits reales de los repositorios separados. `buildInfo.json` declara que contiene la adaptación y no inventa una revisión de `totality`.

Chipper utiliza MIT; se incluye `integrations/phet/LICENSE-Chipper.txt`. Las licencias y créditos de medios y otras dependencias deben acompañar las distribuciones según los avisos originales. No elimines los avisos de terceros incorporados al HTML.

Este repositorio entrega adaptador e instrucciones. Si distribuyes o publicas un HTML adaptado, entrega también las fuentes correspondientes y las instrucciones de construcción conforme a su licencia. El manifest y el instalador identifican las revisiones; no reemplazan por sí solos la entrega de fuentes correspondiente a una distribución binaria.

## Bibliografía y código propio

Se incluyen referencias del capítulo 8 de *Problemas de física y cómo resolverlos* (RACSO, 2009). No se redistribuye el PDF adjunto. La incorporación del corpus al RAG se gestiona aparte del repositorio público.

Las dependencias npm y Python conservan sus licencias. Esta base no define todavía una licencia general para el resto del código original del proyecto de grado.
