from datetime import datetime

import pytest

from controller.dashboard_controller import DashboardController
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorHumedad, SensorNivelDeposito, SensorTemperatura
from model.zona import Zona
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador


def guardar_lecturas(repositorio, *lecturas):
    lote = ListaEnlazada()
    for lectura in lecturas:
        lote.insertar(lectura)
    repositorio.anadir(lote)


def agregar_zona_tecnica(repositorio):
    zona = Zona("Z2", "Zona técnica", "zona_tecnica", "logistica")
    zona.anadir_sensor(SensorNivelDeposito("S6", "Depósito", 50, 20))
    repositorio.anadir(zona)


def test_resumen_usa_la_ultima_lectura_y_el_peor_estado_de_cada_zona(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    carpa = Zona("Z1", "Carpa de hospitalización", "carpa", "carpa")
    carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    carpa.anadir_sensor(SensorHumedad("S2", "Humedad", 60, 70))
    zonas.anadir(carpa)
    agregar_zona_tecnica(zonas)
    zonas.anadir(Zona("Z3", "Exterior", "exterior"))
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    guardar_lecturas(
        lecturas,
        Lectura("Z1", "S1", "temperatura", 33.0, "°C", "2026-11-12T10:00:00"),
        Lectura("Z2", "S6", "nivel_deposito", 20.0, "%", "2026-11-12T10:01:00"),
        Lectura("Z1", "S1", "temperatura", 31.4, "°C", "2026-11-12T10:02:00"),
        Lectura("Z1", "S99", "temperatura", 40.0, "°C", "2026-11-12T10:03:00"),
    )
    dashboard = DashboardController(zonas, lecturas, Simulador(zonas, lecturas, semilla=1))

    resumen = dashboard.resumen()

    assert [zona["id"] for zona in resumen] == ["Z1", "Z2", "Z3"]
    assert (resumen[0]["nombre"], resumen[0]["responsable"], resumen[0]["estado"]) == (
        "Carpa de hospitalización", "carpa", "aviso"
    )
    assert resumen[0]["sensores"] == [
        {"nombre": "Temperatura", "valor": 31.4, "unidad": "°C", "estado": "aviso"},
        {"nombre": "Humedad", "valor": None, "unidad": "%", "estado": "normal"},
    ]
    assert resumen[1]["estado"] == "critico"
    assert resumen[1]["sensores"] == [
        {"nombre": "Depósito", "valor": 20.0, "unidad": "%", "estado": "critico"},
    ]
    assert resumen[2]["responsable"] is None
    assert resumen[2]["sensores"] == []
    assert resumen[2]["estado"] == "normal"
    assert dashboard.contadores() == {"normal": 1, "aviso": 1, "critico": 1}
    assert dashboard.ultima_actualizacion == datetime(2026, 11, 12, 10, 2)


@pytest.mark.parametrize("separados", [False, True], ids=("compartidos", "separados"))
def test_actualizar_muestra_la_ronda_nueva_sin_duplicarla(tmp_path, separados):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    agregar_zona_tecnica(zonas)
    ruta = tmp_path / "lecturas.json"
    lecturas_dashboard = RepositorioLecturas(ruta)
    lecturas_simulador = RepositorioLecturas(ruta) if separados else lecturas_dashboard
    simulador = Simulador(zonas, lecturas_simulador, semilla=1)
    dashboard = DashboardController(zonas, lecturas_dashboard, simulador)

    assert dashboard.resumen()[0]["sensores"][0]["valor"] is None
    assert dashboard.ultima_actualizacion is None
    assert not ruta.exists()

    dashboard.actualizar()
    primero = dashboard.resumen()[0]["sensores"][0]["valor"]
    persistidas = RepositorioLecturas(ruta)
    assert primero == persistidas.ultima("S6").valor
    assert len(persistidas.de_sensor("S6")) == 1

    dashboard.actualizar()
    segundo = dashboard.resumen()[0]["sensores"][0]["valor"]
    persistidas = RepositorioLecturas(ruta)
    assert segundo == persistidas.ultima("S6").valor
    assert segundo < primero  # El depósito baja entre estas dos rondas.
    assert len(persistidas.de_sensor("S6")) == 2
    assert dashboard.ultima_actualizacion == datetime.fromisoformat(
        persistidas.ultima("S6").fecha_hora
    )


def test_inicializar_genera_una_sola_ronda_cuando_faltan_lecturas(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    agregar_zona_tecnica(zonas)
    ruta = tmp_path / "lecturas.json"
    dashboard = DashboardController(
        zonas, RepositorioLecturas(ruta), Simulador(zonas, RepositorioLecturas(ruta), semilla=1)
    )

    dashboard.inicializar()
    dashboard.inicializar()

    persistidas = RepositorioLecturas(ruta)
    assert len(persistidas.de_sensor("S6")) == 1
    assert dashboard.resumen()[0]["sensores"][0]["valor"] == persistidas.ultima("S6").valor


def test_inicializar_sin_sensores_no_crea_fichero_de_lecturas(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    ruta = tmp_path / "lecturas.json"
    lecturas = RepositorioLecturas(ruta)
    dashboard = DashboardController(zonas, lecturas, Simulador(zonas, lecturas, semilla=1))

    dashboard.inicializar()

    assert not ruta.exists()
    assert dashboard.resumen() == []
    assert dashboard.contadores() == {"normal": 0, "aviso": 0, "critico": 0}


def test_inicializar_conserva_historial_aunque_falten_lecturas_de_un_sensor(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    agregar_zona_tecnica(zonas)
    carpa = Zona("Z1", "Carpa", "carpa")
    carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    zonas.anadir(carpa)
    ruta = tmp_path / "lecturas.json"
    lecturas = RepositorioLecturas(ruta)
    guardar_lecturas(
        lecturas, Lectura("Z2", "S6", "nivel_deposito", 88.0, "%", "2026-11-12T10:00:00")
    )
    dashboard = DashboardController(zonas, lecturas, Simulador(zonas, lecturas, semilla=1))
    historial = ruta.read_bytes()

    dashboard.inicializar()

    assert ruta.read_bytes() == historial
    assert dashboard.resumen()[1]["sensores"][0]["valor"] is None
