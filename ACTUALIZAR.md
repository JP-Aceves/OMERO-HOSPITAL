# Cómo actualizar la web de OMERO

**Todo el contenido está en [`data/proyecto.json`](data/proyecto.json).** No hace falta tocar HTML, CSS ni JS.

**Dónde vive:** en la rama `gh-pages` del repo `OMERO-HOSPITAL`, separada del código (no comparte historial con `main` ni `develop`). Publicada en <https://jp-aceves.github.io/OMERO-HOSPITAL/>.

**Flujo:**

```bash
git fetch origin
git switch gh-pages          # la primera vez: git switch -c gh-pages origin/gh-pages
# ...editas data/proyecto.json...
git add data/proyecto.json
git commit -m "OME-XX: actualiza la web con el estado del sprint"
git push
git switch develop           # vuelve al código
```

Cada push a `gh-pages` publica la web sola en 1-2 minutos (Settings → Pages → Deploy from a branch: `gh-pages` / root).

## Verla en local antes de subir

Desde la rama `gh-pages`, en la raíz del repo:

```bash
python3 -m http.server
```

Abre <http://localhost:8000>. (Abrir `index.html` con doble clic no funciona: el navegador bloquea la lectura del JSON.)

Si rompes el JSON (una coma de más, una comilla sin cerrar), la web muestra un aviso rojo diciendo qué falla. Para comprobarlo antes: `python3 -m json.tool data/proyecto.json`.

---

## a) Cambiar el sprint actual

```json
"estado": { "sprintActual": 1, "fase": "S1", "mensaje": "" }
```

Con solo cambiar el número se actualizan el badge del inicio, el sprint resaltado del roadmap y la fila resaltada de la rotación PO/SM. Los sprints anteriores pasan a **Hecho**, el actual a **En curso** y los siguientes a **Pendiente**.

`mensaje` es opcional: si lo rellenas, sustituye el resumen automático que aparece bajo la frase tesis.

## b) Marcar tareas como hechas y actualizar puntos

Dentro de `sprints[n].tareas`, cambia el `estado` (`pendiente` | `en-curso` | `hecho`):

```json
{ "id": "OME-3", "titulo": "Estado del arte", "puntos": 5, "estado": "hecho" }
```

La barra de progreso suma sola los puntos de las tareas en `hecho`. Deja `"puntosHechos": null` para que se calcule; si pones un número, ese número manda.

`puntosTotales` es el total del sprint. Si lo pones a `null`, se calcula sumando los puntos de todas las tareas.

Para quitar la etiqueta "Provisional" cuando se confirme un sprint en el Planning: `"provisional": false`.

## c) Cambiar o añadir mockups

**Sustituir un mockup existente** (lo más rápido): guarda la imagen nueva con el mismo nombre encima de la antigua en `assets/img/` (por ejemplo `03_jefe.png`) y borra su miniatura en `assets/img/thumbs/` o sustitúyela. No hay que tocar el JSON.

Ojo: `03_jefe.png`, `04_carpa.png` y `05_logistica.png` también salen en el hero (`proyecto.capturaHero`) y en las pestañas de roles (`roles[].mockup`), así que se actualizan solos en los tres sitios.

**Añadir uno nuevo:**

1. Copia la imagen a `assets/img/` (mejor < 400 KB).
2. Opcional: una miniatura de ~720 px de ancho en `assets/img/thumbs/`. Si no hay, se usa la imagen grande.
3. Añade a `galeria`:

```json
{ "tipo": "Mockup", "titulo": "Histórico", "src": "assets/img/06_historico.png", "thumb": "", "alt": "Mockup de la pantalla de histórico" }
```

`alt` es obligatorio: describe la imagen para lectores de pantalla. Si algún día añadís otro `tipo` (por ejemplo `Diagrama`), aparecen pestañas para cambiar entre tipos.

## d) Cambiar enlaces

```json
"enlaces": {
  "notion": "https://...",
  "githubProjects": "https://github.com/users/JP-Aceves/projects/1",
  "repositorio": "https://github.com/JP-Aceves/OMERO-HOSPITAL",
  "carpetaCompartida": ""
}
```

Un enlace vacío (`""`) se muestra como botón deshabilitado **"Próximamente"**. La carpeta compartida solo aparece en "Enlaces" cuando tiene URL.

> Usad siempre el enlace **público** de Notion (`...notion.site/...`), no el de `app.notion.com`, que solo funciona para miembros del espacio.

## e) Fecha de "Última actualización"

```json
"meta": { "ultimaActualizacion": "2026-10-20", "version": "0.2.0" }
```

Formato siempre `AAAA-MM-DD`. Cámbiala cada vez que edites el JSON.

---

## Reglas generales

- **Fechas** siempre `AAAA-MM-DD`.
- **Nada inventado**: si un dato no está decidido, deja `""`, `null` o `[]`.
- **Lista vacía = sección oculta.** Si `ods`, `galeria`, `fasesS2`… es `[]`, la sección y su enlace del menú desaparecen.
- La cuenta atrás busca en `calendario` la próxima fecha de tipo `Entrega` o `Defensa` a partir de hoy.
- Para filtrar componentes por zona, cada componente lleva `zonas` con los `id` de `zonas` (`carpa`, `tecnica`, `exterior`, `pasillo`). `zonaTexto` es lo que se ve en la tabla.

## Esquema de `proyecto.json`

| Clave | Tipo | Qué es |
|---|---|---|
| `meta` | `{ ultimaActualizacion, version }` | Pie de página. **Obligatoria** |
| `proyecto` | `{ nombre, titulo, subtitulo, capturaHero{src, alt}, tesis, resumen, contexto, problema, pregunta, alcance, hueco, referencias[] }` | Hero (`capturaHero` = imagen grande del inicio), "El problema", "Qué hace" y panel final (`tesis`). **Obligatoria** |
| `enlaces` | `{ notion, githubProjects, repositorio, carpetaCompartida }` | Botones. **Obligatoria** |
| `estado` | `{ sprintActual (número), fase, mensaje }` | Sprint actual. **Obligatoria** |
| `capacidades` | `[{ verbo, texto }]` | Los 5 verbos |
| `flujoAlerta` | `[{ paso, detalle }]` | Diagrama lectura → actuador |
| `funcionalidades` | `[texto]` | Lista de funcionalidades |
| `roles` | `[{ nombre, detalle, descripcion, sensores[], mockup{src, alt} }]` | Pestañas de rol; `mockup` es la captura que se ve a la derecha |
| `reglaNegocio` | texto | Bajo los roles |
| `zonas` | `[{ id, nombre, detalle?, contenido }]` | Zonas de la maqueta y filtros |
| `componentes` | `[{ nombre, tipo, zonaTexto, zonas[], uso, alerta }]` | Tabla filtrable |
| `notaUmbrales` | texto | Aviso de umbrales provisionales |
| `componentesDescartados` | `[{ nombre, motivo }]` | |
| `arquitectura` | `{ patron, regla, capas[{nombre, descripcion}], modelo[], carpetas (texto), stack[{fase, items[]}], ejemploLectura (objeto) }` | `stack` alimenta la tarjeta de tecnologías y la franja animada bajo el hero |
| `sprints` | `[{ numero, nombre, fechaInicio, fechaFin, entregable, estado, provisional, puntosTotales, puntosHechos, tareas[{ id, titulo, puntos, estado }] }]` | Roadmap. **Obligatoria** |
| `fasesS2` / `cierreS2` | `[texto]` / texto | Segundo semestre |
| `calendario` | `[{ fecha, titulo, tipo }]` | `tipo`: Hito, Entrega, Clase, Revisión, Defensa. **Obligatoria** |
| `contenidoEntregaSprint` | `[texto]` | Qué se entrega en cada sprint |
| `festivos` | `[{ desde, hasta }]` | |
| `empresa` | `{ nombre, tipo, descripcion, metodologia }` | Intro de "Equipo" |
| `equipo` | `[{ nombre, github }]` | `github` sin @; vacío = sin enlace |
| `rotacionScrum` | `[{ sprint, productOwner, scrumMaster }]` | Los nombres deben coincidir con `equipo` |
| `ods` | `[{ numero, nombre, texto }]` | |
| `galeria` | `[{ tipo, titulo, src, thumb, alt }]` | Con lightbox |
| `asignatura` | `{ nombre, grado, universidad, curso, docente, descripcion }` | Pie de página |

Las claves que empiezan por `_` (por ejemplo `enlaces._todo`) son notas para el equipo y la web las ignora.

## Si tocáis el CSS o el JS

El navegador guarda en caché `styles.css` y `app.js`. Si cambiáis alguno, subid el número en `index.html` (`styles.css?v=2` → `?v=3`, `app.js?v=2` → `?v=3`) para que todos vean la versión nueva. Para el JSON no hace falta.
