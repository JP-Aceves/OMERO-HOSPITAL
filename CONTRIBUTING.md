# Cómo trabajamos en OMERO

## Ramas
- `main`: versiones entregadas. Solo recibe merge desde `develop` al cerrar cada sprint.
- `develop`: integración del sprint. Solo recibe Pull Requests revisados.
- `feature/OME-XX`: una rama por tarea. Sale de `develop` y vuelve a `develop` por PR.

## Flujo de una tarea
1. Mueve tu tarjeta a "En progreso" (Notion y GitHub Projects).
2. `git checkout develop && git pull origin develop`
3. `git checkout -b feature/OME-XX`
4. Commits pequeños y frecuentes: `OME-XX: qué hace, en presente`.
5. `git push -u origin feature/OME-XX` y abre un PR hacia `develop` con `Closes #N`.
6. Otro miembro revisa y aprueba. Nadie aprueba su propio PR.
7. Merge, borra la rama y mueve la tarjeta a "Hecho".

## Código
- PEP 8: clases en `PascalCase`, funciones y variables en `snake_case`.
- Cada clase en su capa: `model`, `view`, `controller`, `service`, `persistence`.
- Las vistas nunca leen el JSON: siempre a través de un controlador.
- Cada uno solosus archivos. Si necesitas cambiar algo de otro, avisa antes.
- Antes de abrir un PR: `python main.py` arranca y `pytest` pasa.
