"""Un umbral cambiado se aplica en la siguiente lectura (HU-09). Responsable: JP (OME-64).

Cada pantalla tiene su propio RepositorioZonas: "Zonas y sensores" guarda el
umbral en el JSON y el dashboard lo vuelve a leer antes de la siguiente ronda.
"""
from controller.dashboard_controller import DashboardController
from controller.zonas_controller import ZonasController
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorNivelDeposito, SensorTemperatura
from model.zona import Zona
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas


class SimuladorFijo:
    """Simulador de prueba: cada ronda devuelve siempre el mismo valor."""

    def __init__(self, repo_zonas, valores):
        self.repo_zonas = repo_zonas
        self.valores = valores  # {"S1": ("Z1", "temperatura", 30.0, "°C")}

    def generar_ronda(self):
        ronda = ListaEnlazada()
        for id_sensor, (zona, tipo, valor, unidad) in self.valores.items():
            ronda.insertar(Lectura(zona, id_sensor, tipo, valor, unidad, "2026-11-24T18:30:00"))
        return ronda


def preparar(tmp_path, temperatura=30.0):
    """Carpa con temperatura 28/32 y una lectura de 30 °C (aviso)."""
    ruta = tmp_path / "zonas.json"
    zonas = RepositorioZonas(ruta)
    carpa = Zona("Z1", "Carpa de hospitalización", "carpa", "carpa")
    carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    zonas.anadir(carpa)
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    simulador = SimuladorFijo(RepositorioZonas(ruta), {"S1": ("Z1", "temperatura", temperatura, "°C")})
    dashboard = DashboardController(RepositorioZonas(ruta), lecturas, simulador)
    # "Zonas y sensores" usa otro repositorio, como en main.py
    pantalla_zonas = ZonasController(RepositorioZonas(ruta), RepositorioJSON(tmp_path / "usuarios.json"))
    return dashboard, pantalla_zonas


def estado_carpa(dashboard):
    return dashboard.resumen()[0]["estado"]


def test_subir_el_umbral_se_aplica_en_la_siguiente_lectura(tmp_path):
    dashboard, pantalla_zonas = preparar(tmp_path)
    dashboard.actualizar()
    assert estado_carpa(dashboard) == "aviso"

    assert pantalla_zonas.editar_sensor("Z1", "S1", "Temperatura", "35", "40") is None
    dashboard.actualizar()

    assert estado_carpa(dashboard) == "normal"


def test_bajar_el_umbral_pone_la_carpa_en_critico(tmp_path):
    dashboard, pantalla_zonas = preparar(tmp_path)
    dashboard.actualizar()

    assert pantalla_zonas.editar_sensor("Z1", "S1", "Temperatura", "25", "29") is None
    dashboard.actualizar()

    assert estado_carpa(dashboard) == "critico"


def test_un_umbral_no_valido_no_cambia_nada(tmp_path):
    dashboard, pantalla_zonas = preparar(tmp_path)
    dashboard.actualizar()

    assert pantalla_zonas.editar_sensor("Z1", "S1", "Temperatura", "abc", "40") is not None
    dashboard.actualizar()

    assert estado_carpa(dashboard) == "aviso"


def test_el_dashboard_nuevo_ya_usa_el_umbral_cambiado(tmp_path):
    """Volver a "Estado global" crea un dashboard nuevo (main.py) y también lo ve."""
    dashboard, pantalla_zonas = preparar(tmp_path)
    dashboard.actualizar()
    pantalla_zonas.editar_sensor("Z1", "S1", "Temperatura", "35", "40")

    nuevo = DashboardController(RepositorioZonas(tmp_path / "zonas.json"),
                                RepositorioLecturas(tmp_path / "lecturas.json"), dashboard.simulador)
    nuevo.actualizar()

    assert estado_carpa(nuevo) == "normal"


def test_el_umbral_inverso_tambien_se_aplica(tmp_path):
    """En el depósito (INVERSO) bajar el umbral crítico saca la zona de crítico."""
    ruta = tmp_path / "zonas.json"
    zonas = RepositorioZonas(ruta)
    tecnica = Zona("Z2", "Zona técnica", "zona_tecnica", "logistica")
    tecnica.anadir_sensor(SensorNivelDeposito("S6", "Depósito", 50, 20))
    zonas.anadir(tecnica)
    simulador = SimuladorFijo(RepositorioZonas(ruta), {"S6": ("Z2", "nivel_deposito", 18.0, "%")})
    dashboard = DashboardController(RepositorioZonas(ruta), RepositorioLecturas(tmp_path / "l.json"), simulador)
    pantalla_zonas = ZonasController(RepositorioZonas(ruta), RepositorioJSON(tmp_path / "u.json"))
    dashboard.actualizar()
    assert estado_carpa(dashboard) == "critico"

    assert pantalla_zonas.editar_sensor("Z2", "S6", "Depósito", "30", "15") is None
    dashboard.actualizar()

    assert estado_carpa(dashboard) == "aviso"


def test_recargar_lee_los_cambios_de_otro_repositorio(tmp_path):
    ruta = tmp_path / "zonas.json"
    uno = RepositorioZonas(ruta)
    uno.anadir(Zona("Z1", "Carpa", "carpa"))
    otro = RepositorioZonas(ruta)
    uno.anadir(Zona("Z2", "Exterior", "exterior"))
    assert otro.buscar("Z2") is None

    otro.recargar()

    assert otro.buscar("Z2") is not None
