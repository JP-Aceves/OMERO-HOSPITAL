"""OME-71: las lecturas llegan solas y la pantalla abierta se refresca sin pulsar nada."""
import asyncio
from types import SimpleNamespace

import flet as ft
import pytest

import main as aplicacion
from model.actuador import Actuador
from model.sensor import SensorHumoGas, SensorTemperatura
from model.usuario import JefeSanidad, ResponsableCarpa, TecnicoLogistica, hashear
from model.zona import Zona
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador
from view.actuadores_view import ActuadoresView

CLAVE = "prueba-ome-71"


class _ParaDeLeer(Exception):
    """Corta el bucle infinito de lecturas después de las rondas que pide la prueba."""


class _Pagina:
    """Página falsa: guarda la tarea de lecturas en vez de arrancarla."""

    def __init__(self):
        self.window = SimpleNamespace()
        self.fonts = {}
        self.views = []
        self.tarea = None

    def go(self, ruta):
        self.route = ruta
        self.on_route_change()

    def update(self):
        pass

    def run_task(self, funcion):
        self.tarea = funcion


def _recorrer(control):
    yield control
    for hijo in getattr(control, "controls", None) or ():
        yield from _recorrer(hijo)
    contenido = getattr(control, "content", None)
    if contenido is not None:
        yield from _recorrer(contenido)


def _textos(pagina):
    return {c.value for c in _recorrer(pagina.views[0]) if isinstance(getattr(c, "value", None), str)}


@pytest.fixture
def campamento(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    zonas = RepositorioZonas()
    carpa = Zona("Z1", "Carpa", "carpa", "carpa")
    carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura de la carpa", 28, 32))
    carpa.anadir_actuador(Actuador("A1", "Ventilador", "ventilador"))
    zonas.anadir(carpa)
    tecnica = Zona("Z2", "Zona técnica", "zona_tecnica", "logistica")
    tecnica.anadir_sensor(SensorHumoGas("S2", "MQ-2", 20, 50))
    tecnica.anadir_actuador(Actuador("A2", "LED", "led_evacuacion"))
    zonas.anadir(tecnica)
    cuentas = RepositorioJSON()
    for rol, nombre in ((JefeSanidad, "jefe"), (ResponsableCarpa, "carpa"), (TecnicoLogistica, "logistica")):
        sal, codigo = hashear(CLAVE)
        cuentas.anadir(rol(nombre, nombre, codigo, sal))

    valores = {"S1": 25.0, "S2": 10.0}
    monkeypatch.setattr(Simulador, "_siguiente_valor", lambda _simulador, sensor: valores[sensor.id])
    return valores


def _entrar(nombre):
    pagina = _Pagina()
    aplicacion.main(pagina)
    campos = {c.key: c for c in _recorrer(pagina.views[0]) if getattr(c, "key", None)}
    campos["test:login_usuario"].value = nombre
    campos["test:login_contrasena"].value = CLAVE
    campos["test:login_enviar"].on_click(None)
    return pagina


def _leer(pagina, monkeypatch, rondas=1):
    """Ejecuta el bucle de main.py durante esas rondas, sin esperar de verdad."""
    llamadas = {"n": 0}

    async def sin_esperar(_segundos):
        llamadas["n"] += 1
        if llamadas["n"] > rondas:
            raise _ParaDeLeer

    monkeypatch.setattr(aplicacion.asyncio, "sleep", sin_esperar)
    with pytest.raises(_ParaDeLeer):
        asyncio.run(pagina.tarea())


def test_el_jefe_ve_las_lecturas_nuevas_sin_pulsar_nada(campamento, monkeypatch):
    pagina = _entrar("jefe")
    assert "25 °C" in _textos(pagina)

    campamento["S1"] = 33.0
    _leer(pagina, monkeypatch)

    textos = _textos(pagina)
    assert "33 °C" in textos and "25 °C" not in textos
    assert "1 activa" in textos


def test_el_led_de_evacuacion_cambia_solo_en_el_panel_del_jefe(campamento, monkeypatch):
    pagina = _entrar("jefe")
    assert any(t.endswith("LED · Apagado") for t in _textos(pagina))

    campamento["S2"] = 60.0  # humo crítico: el sistema enciende la evacuación
    _leer(pagina, monkeypatch)

    assert any(t.endswith("LED · Encendido") for t in _textos(pagina))


def test_carpa_y_tecnico_tambien_se_refrescan_solos(campamento, monkeypatch):
    carpa = _entrar("carpa")
    campamento["S1"] = 26.5
    _leer(carpa, monkeypatch)
    assert "26,5 °C" in _textos(carpa)

    tecnico = _entrar("logistica")
    campamento["S2"] = 30.0
    _leer(tecnico, monkeypatch)
    assert "30" in _textos(tecnico)


def test_sin_sesion_no_se_generan_lecturas(campamento, monkeypatch):
    pagina = _Pagina()
    aplicacion.main(pagina)
    _leer(pagina, monkeypatch, rondas=3)

    assert not (pagina.views and any("°C" in t for t in _textos(pagina)))
    from persistence.repositorio_lecturas import RepositorioLecturas
    assert RepositorioLecturas().ultima("S1") is None


def test_el_panel_de_actuadores_ya_no_tiene_boton_de_actualizar(campamento):
    pagina = _entrar("jefe")
    panel = next(c for c in _recorrer(pagina.views[0]) if isinstance(c, ActuadoresView))

    assert not any(isinstance(c, ft.OutlinedButton) and c.text == "Actualizar estados" for c in _recorrer(panel))
