# OMERO · Monitor de Hospital de Campaña

Aplicación de escritorio para supervisar las **condiciones ambientales, los riesgos y los recursos críticos de un hospital de campaña** desplegado en una zona crítica. Cada tipo de usuario ve la información y las acciones que le corresponden, recibe alertas en tiempo real y consulta predicciones sobre el agotamiento de recursos.

Proyecto integrador de **Proyecto de Informática I y II**, Grado en Ingeniería Informática, Universidad Europea de Madrid, curso 2026-27.

---

> - **Landing Page:** [jp-aceves.github.io/OMERO-HOSPITAL](https://jp-aceves.github.io/OMERO-HOSPITAL/)
> - **Notion Workspace:** [Proyecto de Informática · OMERO](https://learningresourcess.notion.site/Proyecto-de-Inform-tica-OMERO-Hospital-de-campa-a-3ed09b9060ac8164be89d91fb4c22605)
> - **GitHub Projects:** [Tablero del proyecto](https://github.com/users/JP-Aceves/projects/3/views/1)

---

## Funcionalidades

- Login único para todos los roles y vista de registro.
- Dashboard diferente para cada rol.
- Lecturas de sensores por zona (carpa, zona técnica, exterior).
- Alertas por umbrales con semáforo verde / amarillo / rojo.
- Histórico de lecturas y gráficas de evolución.
- Predicción por regresión lineal (tiempo restante hasta vaciar el depósito).
- Control del ventilador y de los indicadores LED.
- Interfaz responsive.

## Roles

| Rol | Qué ve |
|---|---|
| **Administrador** | Gestión de las cuentas de usuario |
| **Jefe de sanidad** | Todas las zonas, gestión de zonas y sensores, asignación de responsables, alertas, histórico y predicciones |
| **Responsable de carpa** | Temperatura, humedad, calidad del aire, luz y ventilación de su carpa |
| **Técnico de logística** | Nivel de depósitos, humo/gas, viento, control de actuadores |

## Sensores y actuadores

| Componente | Mide / hace |
|---|---|
| DHT22 | Temperatura y humedad de la carpa |
| MQ-135 | Calidad del aire |
| MQ-2 | Humo y gases inflamables |
| HC-SR04 | Nivel del depósito |
| Anemómetro | Velocidad del viento |
| LDR | Luz (detección de corte de luz) |
| Ventilador 5V | Ventilación automática o manual |
| LEDs | Semáforo de estado, evacuación y luz de emergencia |

En la primera iteración (S1) las lecturas se **simulan** y se guardan en JSON. En la segunda (S2) llegan desde un **ESP32** a una base de datos en red.

---

## Tecnologías

- Python 3.12
- Flet para la interfaz gráfica
- Matplotlib para las gráficas
- `json` de la librería estándar para la persistencia
- pytest para las pruebas
- S2: ESP32 (MicroPython), MQTT (`paho-mqtt`), base de datos SQL

## Requisitos

- Python 3.12 o superior
- IDE recomendado: PyCharm o VS Code

## Instalación y arranque

```bash
git clone https://github.com/JP-Aceves/OMERO-HOSPITAL.git
cd OMERO-HOSPITAL
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

La primera vez que se ejecuta, Flet descarga su aplicación de escritorio y tarda un poco.

Tests: `pytest`

## Estructura

| Carpeta | Qué va dentro |
|---|---|
| `model/` | Clases del dominio (Usuario, Zona, Sensor, Actuador, Lectura, Nodo, ListaEnlazada) |
| `view/` | Pantallas de Flet. Nunca leen el JSON directamente |
| `controller/` | Reciben eventos de las vistas y coordinan |
| `service/` | Lógica reutilizable (simulador, alertas, estadística) |
| `persistence/` | Lectura y escritura de los JSON |
| `data/` | Ficheros JSON |
| `tests/` | Pruebas con pytest |

Normas de trabajo con Git: ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Formato de los datos (A-03)

`data/zonas.json`: cada zona con sus sensores y actuadores. `responsable` es el nombre de usuario asignado (o `null`).

```json
[
  {
    "id": "Z1",
    "nombre": "Carpa de hospitalización",
    "tipo": "carpa",
    "responsable": "carpa",
    "sensores": [
      {"id": "S1", "nombre": "DHT22 temperatura", "tipo": "temperatura", "umbral_aviso": 28, "umbral_critico": 32}
    ],
    "actuadores": [
      {"id": "A1", "nombre": "Ventilador", "tipo": "ventilador", "encendido": false}
    ]
  }
]
```

`data/lecturas.json`: lo genera el simulador (`python -m service.simulador --rondas 50`) y no se sube a Git. Cada lectura tiene el mismo formato que enviará el ESP32 en el segundo semestre.

```json
[
  {"zona": "Z1", "sensor": "S1", "tipo": "temperatura", "valor": 31.4, "unidad": "°C", "fecha_hora": "2026-11-10T18:30:00"}
]
```

**Cómo simula (OME-33).** Cada ronda crea una lectura por sensor: el valor parte de la última lectura guardada, se acerca un 20 % a su valor normal (el centro de la zona verde) y suma una variación aleatoria pequeña; un 5 % de las veces da un pico más allá del umbral crítico (hacia abajo en los sensores INVERSO) y en la ronda siguiente vuelve a lo normal. El depósito no tiene picos: solo baja entre 0,5 y 2 puntos por ronda y se rellena al 90-100 % cuando baja del 10 %. Opciones: `--rondas`, `--minutos` (separación entre rondas, 5 por defecto) y `--semilla` (mismos valores en cada ejecución); si ya hay lecturas se añaden detrás, así que para empezar de cero borra `data/lecturas.json`.

## Umbrales (fuente: tabla "Umbrales iniciales por sensor" del documento del proyecto)

| `tipo` | Sensor | Unidad | Aviso | Crítico | Malo si | Rango simulado |
|---|---|---|---|---|---|---|
| `temperatura` | DHT22 | °C | 28 | 32 | sube | 15 a 45 |
| `humedad` | DHT22 | % | 60 | 70 | sube | 20 a 95 |
| `calidad_aire` | MQ-135 | % sobre la base | 20 | 50 | sube | 0 a 100 |
| `humo_gas` | MQ-2 | % sobre la base | 20 | 50 | sube | 0 a 100 |
| `viento` | Anemómetro | km/h | 30 | 50 | sube | 0 a 90 |
| `luz` | LDR | % | 40 | 20 | **baja** (`INVERSO`) | 0 a 100 |
| `nivel_deposito` | HC-SR04 | % | 50 | 20 | **baja** (`INVERSO`) | 0 a 100 |

- Los MQ, sin calibrar, no dan ppm exactos: se mide el % por encima del valor base en aire limpio.
- La humedad también es mala por debajo de 30 % (aviso) y 20 % (crítico); ese lado se añade en el Sprint 3 (HU-09).
- Estado de un sensor: si no es inverso, a partir del crítico es crítico y a partir del aviso es aviso; si es inverso, igual hacia abajo. El estado de una zona es el peor de sus sensores.
- Si cambia un umbral, se cambia en el documento del proyecto y aquí, en ningún otro sitio.

Tipos de zona: `carpa`, `zona_tecnica`, `exterior`. Tipos de actuador: `ventilador`, `led_semaforo`, `led_evacuacion`.

## Roadmap S1

- [x] Sprint 0 · Anteproyecto, Product Backlog y mockups
- [x] Sprint 1 · Estructura base y autenticación (`v0.1-sprint1`)
- [ ] Sprint 2 · Gestión de datos (CRUD) y simulador de sensores
- [ ] Sprint 3 · Dashboards, alertas y estadística
- [ ] Sprint 4 · Optimización y entrega final

## Equipo OMERO

| Nombre | GitHub |
|---|---|
| Alejandro Medina | @roca200300 |
| Jose Aceves | @JP-Aceves |
| Alejandro Rodas | @AlejandroRodasSamblasUniversidadEuropea |
| Ivan Sanz | @ivansnzlpz |

Docente: Jorge García González

## Licencia

Proyecto académico. Uso educativo.