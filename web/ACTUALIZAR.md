# Cómo actualizar la web de OMERO

**Todo el contenido está en [`data/proyecto.json`](data/proyecto.json).** No hace falta tocar HTML, CSS ni JS.

Flujo: rama `feature/OME-XX-...` → editas el JSON → PR a `develop` → al hacer merge, GitHub Actions publica la web sola (1-2 min).

## Verla en local antes de subir

```bash
cd web
python3 -m http.server
```

Abre <http://localhost:8000>. (Abrir `index.html` con doble clic no funciona: el navegador bloquea la lectura del JSON.)

Si rompes el JSON (una coma de más, una comilla sin cerrar), la web muestra un aviso rojo diciendo qué falla. Para comprobarlo antes: `python3 -m json.tool web/data/proyecto.json`.

---

## a) Cambiar el sprint actual

```json
"estado": { "sprintActual": 1, "fase": "S1", "mensaje": "" }
```

Con solo cambiar el número se actualizan el badge del inicio, el sprint resaltado del roadmap, la fila de PO/SM y el rol de cada persona en "Equipo". Los sprints anteriores pasan a **Hecho**, el actual a **En curso** y los siguientes a **Pendiente**.

`mensaje` es opcional: si lo rellenas, sustituye el resumen automático que aparece bajo la frase tesis.

## b) Marcar tareas como hechas y actualizar puntos

Dentro de `sprints[n].tareas`, cambia el `estado` (`pendiente` | `en-curso` | `hecho`):

```json
{ "id": "OME-3", "titulo": "Estado del arte", "puntos": 5, "estado": "hecho" }
```

La barra de progreso suma sola los puntos de las tareas en `hecho`. Deja `"puntosHechos": null` para que se calcule; si pones un número, ese número manda.

`puntosTotales` es el total del sprint. Si lo pones a `null`, se calcula sumando los puntos de todas las tareas.

Para quitar la etiqueta "Provisional" cuando se confirme un sprint en el Planning: `"provisional": false`.

## c) Añadir una decisión

Añade un objeto al final de `decisiones` (la coma va **entre** objetos, no después del último):

```json
{ "fecha": "2026-10-20", "decision": "Umbrales de temperatura de la carpa", "estado": "Aceptada", "motivo": "Acordado en el Sprint Planning 1" }
```

`estado`: `Aceptada` o `Descartada`. Si cierra algo de `pendientes`, bórralo de esa lista.

## d) Añadir una imagen a la galería

1. Copia la imagen a `web/assets/img/` (mejor < 400 KB; PNG para diagramas, JPG para capturas).
2. Opcional: una miniatura de ~720 px de ancho en `web/assets/img/thumbs/`. Si no hay, se usa la imagen grande.
3. Añade a `galeria`:

```json
{ "tipo": "Diagrama", "titulo": "Secuencia: login", "src": "assets/img/secuencia_login.png", "thumb": "", "alt": "Diagrama de secuencia del login" }
```

`tipo` agrupa las imágenes (`Mockup`, `Diagrama`…). `alt` es obligatorio: describe la imagen para lectores de pantalla.

## e) Cambiar enlaces

```json
"enlaces": {
  "notion": "https://...",
  "githubProjects": "https://github.com/users/JP-Aceves/projects/1",
  "repositorio": "https://github.com/JP-Aceves/OMERO-HOSPITAL",
  "carpetaCompartida": ""
}
```

Un enlace vacío (`""`) se muestra como botón deshabilitado **"Próximamente"**. La carpeta compartida solo aparece en "Enlaces" cuando tiene URL.

> **Notion es privado.** Para que lo vea alguien de fuera del equipo: en Notion → Compartir → *Publicar en la web*, y pega aquí la URL pública.

## f) Fecha de "Última actualización"

```json
"meta": { "ultimaActualizacion": "2026-10-20", "version": "0.2.0" }
```

Formato siempre `AAAA-MM-DD`. Cámbiala cada vez que edites el JSON.

---

## Reglas generales

- **Fechas** siempre `AAAA-MM-DD`.
- **Nada inventado**: si un dato no está decidido, deja `""`, `null` o `[]`.
- **Lista vacía = sección oculta.** Si `ods`, `galeria`, `decisiones`… es `[]`, la sección y su enlace del menú desaparecen.
- La cuenta atrás busca en `calendario` la próxima fecha de tipo `Entrega` o `Defensa` a partir de hoy.
- Para filtrar componentes por zona, cada componente lleva `zonas` con los `id` de `zonas` (`carpa`, `tecnica`, `exterior`, `pasillo`). `zonaTexto` es lo que se ve en la tabla.

## Esquema de `proyecto.json`

| Clave | Tipo | Qué es |
|---|---|---|
| `meta` | `{ ultimaActualizacion, version }` | Pie de página. **Obligatoria** |
| `proyecto` | `{ nombre, titulo, subtitulo, tesis, resumen, contexto, problema, pregunta, alcance, hueco, referencias[] }` | Hero, "El problema" y "Qué hace". **Obligatoria** |
| `enlaces` | `{ notion, githubProjects, repositorio, carpetaCompartida }` | Botones. **Obligatoria** |
| `estado` | `{ sprintActual (número), fase, mensaje }` | Sprint actual. **Obligatoria** |
| `capacidades` | `[{ verbo, texto }]` | Los 5 verbos |
| `flujoAlerta` | `[{ paso, detalle }]` | Diagrama lectura → actuador |
| `funcionalidades` | `[texto]` | Lista de funcionalidades |
| `roles` | `[{ nombre, detalle, descripcion, sensores[] }]` | Tarjetas de rol |
| `reglaNegocio` | texto | Bajo los roles |
| `zonas` | `[{ id, nombre, detalle?, contenido }]` | Zonas de la maqueta y filtros |
| `componentes` | `[{ nombre, tipo, zonaTexto, zonas[], uso, alerta }]` | Tabla filtrable |
| `notaUmbrales` | texto | Aviso de umbrales provisionales |
| `componentesDescartados` | `[{ nombre, motivo }]` | |
| `arquitectura` | `{ patron, regla, capas[{nombre, descripcion}], modelo[], carpetas (texto), stack[{fase, items[]}], ejemploLectura (objeto) }` | |
| `sprints` | `[{ numero, nombre, fechaInicio, fechaFin, entregable, estado, provisional, puntosTotales, puntosHechos, tareas[{ id, titulo, puntos, estado }] }]` | Roadmap. **Obligatoria** |
| `fasesS2` / `cierreS2` | `[texto]` / texto | Segundo semestre |
| `calendario` | `[{ fecha, titulo, tipo }]` | `tipo`: Hito, Entrega, Clase, Revisión, Defensa. **Obligatoria** |
| `contenidoEntregaSprint` | `[texto]` | Qué se entrega en cada sprint |
| `festivos` | `[{ desde, hasta }]` | |
| `empresa` | `{ nombre, tipo, descripcion, metodologia }` | Intro de "Equipo" |
| `equipo` | `[{ nombre, github }]` | `github` sin @; vacío = sin enlace |
| `rotacionScrum` | `[{ sprint, productOwner, scrumMaster }]` | Los nombres deben coincidir con `equipo` |
| `decisiones` | `[{ fecha, decision, estado, motivo }]` | |
| `pendientes` | `[texto]` | Bloque "Abierto" |
| `ods` | `[{ numero, nombre, texto }]` | |
| `galeria` | `[{ tipo, titulo, src, thumb, alt }]` | Con lightbox |
| `asignatura` | `{ nombre, grado, universidad, curso, docente, descripcion }` | Pie de página |

Las claves que empiezan por `_` (por ejemplo `enlaces._todo`) son notas para el equipo y la web las ignora.
