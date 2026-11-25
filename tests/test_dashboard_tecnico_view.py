"""Pruebas de la pantalla "Recursos y riesgos" del técnico de logística (OME-63)."""
import asyncio
from datetime import datetime
from pathlib import Path
from shutil import copyfile

import flet as ft
import pytest

from controller.actuadores_controller import ActuadoresController
from controller.dashboard_controller import DashboardController
from controller.tecnico_controller import TecnicoController
from model.usuario import TecnicoLogistica
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador
from view.dashboard_tecnico_view import DashboardTecnicoView, momento_actualizacion, numero, tiempo_restante

NORMALES = {
    "temperatura": 25, "humedad": 50, "calidad_aire": 10, "luz": 60,
    "humo_gas": 5, "nivel_deposito": 80, "viento": 10,
}


def _controles(control):
    yield control
    for hijo in getattr(control, "controls", None) or []:
        yield from _controles(hijo)
    contenido = getattr(control, "content", None)
    if isinstance(contenido, ft.Control):
        yield from _controles(contenido)


def _textos(control):
    return [e.value for e in _controles(control) if isinstance(e, ft.Text) and e.visible]


def _por_clave(control, clave):
    return next(e for e in _controles(control) if e.key == clave)


def _boton(control, texto):
    return next(e for e in _controles(control) if getattr(e, "text", None) == texto)


@pytest.fixture
def contexto(tmp_path, monkeypatch):
    origen = Path(__file__).resolve().parents[1] / "data" / "zonas.json"
    ruta_zonas = tmp_path / "zonas.json"
    copyfile(origen, ruta_zonas)
    ruta_lecturas = tmp_path / "lecturas.json"
    zonas = RepositorioZonas(ruta_zonas)
    # Todos los actuadores empiezan apagados, aunque data/zonas.json haya cambiado al usar la app.
    for zona in zonas.listar():
        for actuador in zona.actuadores:
            actuador.apagar()
    zonas.guardar()
    simulador = Simulador(zonas, RepositorioLecturas(ruta_lecturas), semilla=7)
    valores = dict(NORMALES)
    niveles = []

    def siguiente_valor(sensor):
        if sensor.TIPO == "nivel_deposito" and niveles:
            return niveles.pop(0)
        return valores[sensor.TIPO]

    monkeypatch.setattr(simulador, "_siguiente_valor", siguiente_valor)
    controlador = TecnicoController(
        DashboardController(zonas, RepositorioLecturas(ruta_lecturas), simulador),
        ActuadoresController(RepositorioZonas(ruta_zonas)),
        RepositorioLecturas(ruta_lecturas),
    )
    return controlador, simulador, valores, niveles


def _vista(controlador, usuario="logistica"):
    return DashboardTecnicoView(TecnicoLogistica("Técnico", usuario, "", ""), controlador)


def test_formatos():
    assert numero(31.4) == "31,4" and numero(40.0) == "40" and numero(-15.1612) == "-15,2"
    assert tiempo_restante(545) == "9 h 5 min" and tiempo_restante(35) == "35 min"
    assert tiempo_restante(8318) == "5 d 18 h"


def test_la_hora_de_actualizacion_lleva_fecha_si_no_es_de_hoy():
    hoy = datetime(2026, 11, 25, 19, 10)
    assert momento_actualizacion(datetime(2026, 11, 25, 19, 9), hoy) == " · actualizado a las 19:09"
    assert momento_actualizacion(datetime(2026, 11, 20, 19, 9), hoy) == " · actualizado el 20/11 a las 19:09"
    assert momento_actualizacion(None, hoy) == " · sin lecturas todavía"


def test_muestra_deposito_humo_viento_y_la_grafica_con_la_prediccion(contexto):
    controlador, simulador, _, niveles = contexto
    niveles.extend([90, 88, 86, 84, 82, 80])
    simulador.generar(6, 10)

    contenido = _vista(controlador).construir()
    textos = _textos(contenido)

    assert "Recursos y riesgos" in textos
    assert {"Depósito de agua", "MQ-2 humo y gas", "Anemómetro viento"} <= set(textos)
    # Baja 2 puntos cada 10 minutos: del 80 % al 0 % quedan 400 minutos.
    assert _por_clave(contenido, "tecnico_restante").value == "6 h 40 min"
    assert "Predicción por regresión lineal (-12 % por hora)" in textos
    assert "Aviso 30 km/h · crítico 50 km/h" in textos
    _por_clave(contenido, "tecnico_grafica")


def test_sin_cinco_lecturas_explica_por_que_no_hay_prediccion(contexto):
    controlador, _, _, _ = contexto

    contenido = _vista(controlador).construir()

    assert _por_clave(contenido, "tecnico_restante").value == "Sin predicción"
    assert "Hacen falta 5 lecturas desde el último rellenado." in _textos(contenido)


def test_humo_critico_avisa_arriba(contexto):
    controlador, _, valores, _ = contexto
    valores["humo_gas"] = 60

    textos = _textos(_vista(controlador).construir())

    assert "Crítico: MQ-2 humo y gas" in textos


def test_el_boton_de_evacuacion_enciende_y_apaga_el_led(contexto):
    controlador, _, _, _ = contexto
    usuario = TecnicoLogistica("Técnico", "logistica", "", "")
    contenido = _vista(controlador).construir()

    asyncio.run(_boton(contenido, "Activar evacuación").on_click(None))
    assert controlador.led_evacuacion(usuario)["encendido"] is True
    assert "LEDs de evacuación: encendidos" in _textos(contenido)

    asyncio.run(_boton(contenido, "Desactivar evacuación").on_click(None))
    assert controlador.led_evacuacion(usuario)["encendido"] is False


def test_actualizar_cambia_los_valores(contexto):
    controlador, _, valores, _ = contexto
    contenido = _vista(controlador).construir()
    assert "10" in _textos(contenido)

    valores["viento"] = 42
    asyncio.run(_boton(contenido, "Actualizar").on_click(None))

    textos = _textos(contenido)
    assert "42" in textos and "Aviso" in textos


def test_sin_zonas_asignadas(contexto):
    controlador, _, _, _ = contexto

    contenido = _vista(controlador, usuario="sin_asignar").construir()

    assert "No tienes ninguna zona asignada." in _textos(contenido)
    assert _boton(contenido, "Actualizar").disabled is True