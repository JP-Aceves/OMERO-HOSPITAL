# Cómo trabajamos en OMERO

## Ramas
- `main`: versiones entregadas. Solo recibe merge desde `development` al cerrar cada sprint, con su tag (`v0.2-sprint2`).
- `production`: versión publicada. Solo recibe merge desde `main`.
- `development`: integración del sprint. Solo recibe Pull Requests revisados.
- `feature/OME-XX`: una rama por tarea. Sale de `development` y vuelve a `development` por PR.

## Flujo de una tarea
1. Mueve tu tarjeta a "En progreso" (Notion y GitHub Projects).
2. `git checkout development && git pull origin development`
3. `git checkout -b feature/OME-XX`
4. Commits pequeños y frecuentes: `OME-XX: qué hace, en presente`.
5. `git push -u origin feature/OME-XX` y abre un PR hacia `development` con `Closes #N`.
6. Otro miembro revisa y aprueba. Nadie aprueba su propio PR.
7. Merge y mueve la tarjeta a "Hecho" el mismo día. La rama no se borra hasta después de la entrega del sprint.

## Código
- PEP 8: clases en `PascalCase`, funciones y variables en `snake_case`.
- Cada clase en su capa: `model`, `view`, `controller`, `service`, `persistence`.
- Las vistas nunca leen el JSON: siempre a través de un controlador.
- Cada uno toca solo sus archivos. Si necesitas cambiar algo de otro, avisa antes.
- Antes de abrir un PR: `git pull origin development` en tu rama, `pytest` pasa y `python main.py` arranca.
- Quien revisa un PR ejecuta la app y prueba el cambio a mano, no solo los tests.
- Colores, fuentes y botones siempre desde `view/tema.py`.
