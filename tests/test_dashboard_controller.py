from datetime import datetime
import json
from pathlib import Path

import pytest

from controller.dashboard_controller import DashboardController
from model.actuador import Actuador
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorHumedad, SensorLuz, SensorNivelDeposito, SensorTemperatura
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


class _ZonasDelSimuladorDePrueba:
    def recargar(self):
        pass  # este simulador de prueba no usa zonas


class SimuladorDePrueba:
    def __init__(self, repositorio, rondas):
        self.repositorio = repositorio
        self.repo_zonas = _ZonasDelSimuladorDePrueba()  # OME-64 lo recarga en actualizar()
        self.rondas = iter(rondas)
        self.llamadas = 0

    def generar_ronda(self):
        valores = next(self.rondas)
        self.llamadas += 1
        lecturas = ListaEnlazada()
        for sensor, tipo, unidad, valor in (
            ("S1", "temperatura", "°C", valores[0]),
            ("S2", "luz", "%", valores[1]),
            ("S3", "nivel_deposito", "%", valores[2]),
        ):
            lecturas.insertar(Lectura(
                "Z1", sensor, tipo, valor, unidad,
                f"2026-11-20T18:{self.llamadas:02d}:00",
            ))
        self.repositorio.anadir(lecturas)
        return lecturas


@pytest.fixture
def contexto_semaforos(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    zona = Zona("Z1", "Carpa de prueba", "carpa", "carpa")
    zona.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    zona.anadir_sensor(SensorLuz("S2", "Luz", 40, 20))
    zona.anadir_sensor(SensorNivelDeposito("S3", "Depósito", 50, 20))
    zona.anadir_actuador(Actuador("A1", "Semáforo de entrada", "led_semaforo"))
    zona.anadir_actuador(Actuador("A2", "Semáforo interior", "led_semaforo", True))
    zona.anadir_actuador(Actuador("A3", "Ventilador", "ventilador", True))
    zona.anadir_actuador(Actuador("A4", "Evacuación", "led_evacuacion"))
    zonas.anadir(zona)
    return zonas, RepositorioLecturas(tmp_path / "lecturas.json")


def comprobar_semaforos(zona, esperado):
    actuadores = {actuador.id: actuador for actuador in zona.actuadores}
    for id_semaforo in ("A1", "A2"):
        assert actuadores[id_semaforo].estado == esperado
        assert actuadores[id_semaforo].encendido is True
    return actuadores


@pytest.mark.parametrize(
    ("valores", "esperado"),
    [
        ((25, 80, 95), "normal"),
        ((28, 80, 95), "aviso"),
        ((32, 80, 95), "critico"),
        ((25, 40, 95), "aviso"),
        ((25, 20, 95), "critico"),
        ((25, 80, 50), "aviso"),
        ((25, 80, 20), "critico"),
        ((32, 40, 50), "critico"),
    ],
    ids=(
        "verde", "amarillo-temperatura", "rojo-temperatura", "amarillo-luz",
        "rojo-luz", "amarillo-deposito", "rojo-deposito", "prevalece-rojo",
    ),
)
def test_actualizar_sincroniza_los_dos_semaforos_y_persiste(
    contexto_semaforos, valores, esperado
):
    zonas, lecturas = contexto_semaforos
    otros_antes = {
        actuador.id: actuador.to_dict()
        for actuador in zonas.buscar("Z1").actuadores
        if actuador.tipo != "led_semaforo"
    }
    dashboard = DashboardController(
        zonas, lecturas, SimuladorDePrueba(lecturas, [valores])
    )

    dashboard.actualizar()

    assert dashboard.resumen()[0]["estado"] == esperado
    comprobar_semaforos(dashboard.repo_zonas.buscar("Z1"), esperado)
    recargada = RepositorioZonas(zonas.ruta).buscar("Z1")
    actuadores = comprobar_semaforos(recargada, esperado)
    assert {id_act: actuadores[id_act].to_dict() for id_act in ("A3", "A4")} == otros_antes


def test_inicializar_actualiza_semaforos_con_historial_sin_generar_ronda(contexto_semaforos):
    zonas, lecturas = contexto_semaforos
    guardar_lecturas(
        lecturas, Lectura("Z1", "S3", "nivel_deposito", 20, "%", "2026-11-20T17:00:00")
    )
    historial = lecturas.ruta.read_bytes()
    simulador = SimuladorDePrueba(lecturas, [])
    dashboard = DashboardController(zonas, lecturas, simulador)

    dashboard.inicializar()

    assert simulador.llamadas == 0
    assert lecturas.ruta.read_bytes() == historial
    comprobar_semaforos(RepositorioZonas(zonas.ruta).buscar("Z1"), "critico")


def test_resumen_no_guarda_y_un_estado_igual_no_vuelve_a_guardar(
    contexto_semaforos, monkeypatch
):
    zonas, lecturas = contexto_semaforos
    simulador = SimuladorDePrueba(lecturas, [(25, 80, 95), (26, 75, 90)])
    dashboard = DashboardController(zonas, lecturas, simulador)
    reemplazar_original = Path.replace
    guardados = []

    def reemplazar(temporal, destino):
        if destino == zonas.ruta:
            guardados.append(temporal)
        return reemplazar_original(temporal, destino)

    monkeypatch.setattr(Path, "replace", reemplazar)

    dashboard.resumen()
    assert guardados == []
    dashboard.actualizar()
    assert len(guardados) == 1
    assert guardados[0].parent == zonas.ruta.parent
    assert guardados[0].name.startswith(f".{zonas.ruta.name}-")
    assert guardados[0].suffix == ".tmp"
    assert not guardados[0].exists()
    assert dashboard.repo_zonas.ruta == zonas.ruta
    assert zonas.ruta.exists()
    dashboard.actualizar()
    dashboard.inicializar()
    dashboard.resumen()
    assert len(guardados) == 1
    assert dashboard.repo_zonas.ruta == zonas.ruta


def test_error_al_guardar_semaforos_no_deja_un_estado_falso_en_memoria_y_se_reintenta(
    contexto_semaforos, monkeypatch
):
    zonas, lecturas = contexto_semaforos
    dashboard = DashboardController(
        zonas, lecturas, SimuladorDePrueba(lecturas, [(33, 80, 95)])
    )
    reemplazar_original = Path.replace
    original_json = zonas.ruta.read_bytes()
    fallar = True

    def reemplazar(temporal, destino):
        nonlocal fallar
        if fallar and destino == zonas.ruta:
            fallar = False
            raise OSError("No se puede escribir el estado del semáforo")
        return reemplazar_original(temporal, destino)

    monkeypatch.setattr(Path, "replace", reemplazar)

    with pytest.raises(OSError):
        dashboard.actualizar()

    assert zonas.ruta.read_bytes() == original_json
    assert dashboard.repo_zonas is zonas
    for actuador in dashboard.repo_zonas.buscar("Z1").actuadores:
        if actuador.tipo == "led_semaforo":
            assert actuador.estado is None
    assert len(RepositorioLecturas(lecturas.ruta).de_sensor("S1")) == 1

    dashboard.inicializar()

    comprobar_semaforos(RepositorioZonas(zonas.ruta).buscar("Z1"), "critico")
    assert len(RepositorioLecturas(lecturas.ruta).de_sensor("S1")) == 1


def test_sincronizar_conserva_ediciones_de_otro_repositorio(contexto_semaforos):
    zonas, lecturas = contexto_semaforos
    dashboard = DashboardController(
        zonas, lecturas, SimuladorDePrueba(lecturas, [(31, 80, 95)])
    )
    otro_repositorio = RepositorioZonas(zonas.ruta)
    editada = otro_repositorio.buscar("Z1")
    editada.responsable = "responsable_nuevo"
    editada.buscar_sensor("S1").umbral_aviso = 26
    editada.buscar_sensor("S1").umbral_critico = 30
    for actuador in editada.actuadores:
        if actuador.tipo == "ventilador":
            actuador.apagar()
    otro_repositorio.actualizar(editada)

    dashboard.actualizar()

    recargada = RepositorioZonas(zonas.ruta).buscar("Z1")
    assert recargada.responsable == "responsable_nuevo"
    assert recargada.buscar_sensor("S1").umbral_aviso == 26
    assert recargada.buscar_sensor("S1").umbral_critico == 30
    actuadores = comprobar_semaforos(recargada, "critico")
    assert actuadores["A3"].encendido is False
    assert dashboard.resumen()[0]["estado"] == "critico"


def test_guardado_parcial_no_corrompe_json_limpia_temporal_y_permite_reintentar(
    contexto_semaforos, monkeypatch
):
    zonas, lecturas = contexto_semaforos
    simulador = SimuladorDePrueba(lecturas, [(33, 80, 95)])
    dashboard = DashboardController(zonas, lecturas, simulador)
    volcar_original = json.dump
    original_json = zonas.ruta.read_bytes()
    fallar = True

    def volcar_incompleto(datos, fichero, **opciones):
        nonlocal fallar
        if fallar and Path(fichero.name).name.startswith(f".{zonas.ruta.name}-"):
            fallar = False
            fichero.write('[{"id": "Z1",')
            raise OSError("La escritura se interrumpió a mitad del JSON")
        volcar_original(datos, fichero, **opciones)

    monkeypatch.setattr(json, "dump", volcar_incompleto)

    with pytest.raises(OSError):
        dashboard.actualizar()

    assert zonas.ruta.read_bytes() == original_json
    assert json.loads(zonas.ruta.read_text(encoding="utf-8")) == json.loads(original_json)
    assert not list(zonas.ruta.parent.glob("*.tmp"))
    assert dashboard.repo_zonas is zonas
    assert dashboard.repo_zonas.ruta == zonas.ruta
    assert all(
        actuador.estado is None
        for actuador in dashboard.repo_zonas.buscar("Z1").actuadores
        if actuador.tipo == "led_semaforo"
    )

    dashboard.inicializar()

    comprobar_semaforos(RepositorioZonas(zonas.ruta).buscar("Z1"), "critico")
    assert dashboard.repo_zonas.ruta == zonas.ruta
    assert not list(zonas.ruta.parent.glob("*.tmp"))
    assert simulador.llamadas == 1
    assert len(RepositorioLecturas(lecturas.ruta).de_sensor("S1")) == 1
