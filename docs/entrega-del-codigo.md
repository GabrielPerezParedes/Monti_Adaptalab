# Incorporar esta base al repositorio

La implementación se prepara en `feat/monti-1.1.0`, a partir del commit original `30dbe32b1307c312b452b7ea1051924a4e0a8a25`. Mantén esta rama hasta revisar el versión 1.1.0.

## ZIP

Extrae la carpeta y sigue su README. Contiene fuentes, pruebas, documentación y versiones; no contiene dependencias instaladas, claves, bases de datos ni PhET compilado.

Para incorporarla a un clon de GitHub, crea una rama, copia los archivos del ZIP y revisa `git diff` antes de confirmar. Conserva los archivos de configuración incluidos. Si tienes modificaciones propias, guárdalas en un commit antes de integrar la entrega.

## Git bundle

El bundle conserva los commits. Crea una copia completa:

```bash
git clone PG_AdaptaLab-2D-v1.1.0.bundle PG_AdaptaLab-2D
cd PG_AdaptaLab-2D
git switch feat/monti-1.1.0
git remote set-url origin https://github.com/GabrielPerezParedes/PG_AdaptaLab-2D.git
```

Después de probarla, publica desde tu equipo con tu sesión de GitHub:

```bash
git push -u origin feat/monti-1.1.0
```

También puedes traer la rama a una copia existente:

```bash
git fetch RUTA/PG_AdaptaLab-2D-v1.1.0.bundle feat/monti-1.1.0:feat/monti-1.1.0
git switch feat/monti-1.1.0
```

Sustituye `RUTA` por la carpeta de descarga. Pon la ruta entre comillas si contiene espacios. No necesitas modificar `main` para probar la rama.
