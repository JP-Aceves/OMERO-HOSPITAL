# OMERO · Monitor de Hospital de Campaña

Aplicación de escritorio para supervisar las **condiciones ambientales, los riesgos y los recursos críticos de un hospital de campaña** desplegado en una zona crítica. Cada tipo de usuario ve la información y las acciones que le corresponden, recibe alertas en tiempo real y consulta predicciones sobre el agotamiento de recursos.

Proyecto integrador de **Proyecto de Informática I y II**, Grado en Ingeniería Informática, Universidad Europea de Madrid, curso 2026-27.

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
| **Jefe de sanidad** | Todas las zonas, alertas, histórico, predicciones, gestión de usuarios |
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

## Arquitectura

Patrón **Modelo-Vista-Controlador**, todo en Python.

```
omero_hospital/
├── main.py                   # Punto de entrada
├── model/
│   ├── usuarios.py           # Usuario, JefeSanidad, ResponsableCarpa, TecnicoLogistica
│   ├── sensores.py           # Sensor y subclases
│   ├── actuadores.py         # Actuador, Ventilador, IndicadorLED
│   ├── estructuras.py        # ListaEnlazada, Nodo
│   └── dominio.py            # Zona, Lectura, Alerta, Umbral
├── view/                     # Ventanas y widgets (una vista por pantalla/rol)
├── controller/               # Un controlador por vista
├── service/                  # alertas.py, estadistica.py, simulador.py
├── persistence/              # repositorio_json.py
└── assets/                   # Estilos (identidad OMERO), iconos

data/                         # Ficheros JSON (usuarios, zonas, sensores, lecturas)
tests/                        # Pruebas con pytest
docs/                         # Memoria, UML, mockups, actas
```

## Tecnologías

- Python 3.12
- PySide6 (Qt for Python) para la interfaz gráfica
- Matplotlib para las gráficas
- `json` de la librería estándar para la persistencia
- pytest para las pruebas
- S2: ESP32 (MicroPython), MQTT (`paho-mqtt`), base de datos SQL

## Requisitos

- Python 3.12 o superior
- IDE recomendado: PyCharm o VS Code

## Instalación y ejecución

```bash
git clone https://github.com/omero-uem/omero-hospital-campana.git
cd omero-hospital-campana
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m omero_hospital.main
```

Ejecutar las pruebas:

```bash
pytest
```

Usuarios de prueba en `data/usuarios.json`.

## Formato de una lectura

```json
{
  "idSensor": "MQ135-CARPA1",
  "zona": "CARPA1",
  "tipo": "CALIDAD_AIRE",
  "valor": 412,
  "unidad": "ppm_aprox",
  "timestamp": "2026-10-05T10:15:00"
}
```

---

## Metodología

- **SCRUM** con sprints de 2 semanas.
- Product Backlog en **Trello**.
- Flujo Git: `main` (entregas) ← `develop` (integración) ← `feature/OME-XX-descripcion`.
- Todo cambio entra por Pull Request con revisión de otro miembro.
- Guía completa en [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap S1

- [ ] Sprint 0 · Anteproyecto, Product Backlog y mockups
- [ ] Sprint 1 · Estructura base y autenticación
- [ ] Sprint 2 · Gestión de datos (CRUD) y simulador de sensores
- [ ] Sprint 3 · Dashboards, alertas y estadística
- [ ] Sprint 4 · Optimización y entrega final

## Equipo OMERO

| Nombre | GitHub |
|---|---|
| Alejandro Medina | @roca200300 |
| Jose Aceves | @JP-Aceves |
| Alejandro Rodas | @usuario |
| Ivan Sanz | @usuario |

Docente: Jorge García González

## Licencia

Proyecto académico. Uso educativo.
