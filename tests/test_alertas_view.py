import asyncio
from unittest.mock import Mock

import flet as ft
import pytest

from model.lista_enlazada import ListaEnlazada
from model.usuario import JefeSanidad, ResponsableCarpa, TecnicoLogistica
from service.estado import AVISO, CRITICO, NORMAL
from view.alertas_view import AlertasView
from view.dashboard_jefe_view import DashboardJefeView
from view.inicio_view import InicioView


def _alerta(zona="Carpa de hospitalización", sensor="Temperatura", valor=33.2, nivel=CRITICO):
    return {
        "zona": "Z1", "zona_nombre": zona, "sensor": "S1", "sensor_nombre": sensor,
        "valor": valor, "unidad": "°C", "nivel": nivel,
        "fecha_hora": "2026-11-24T18:30:00",
    }


def _controles(control):
    yield control
    for hijo in getattr(control, "controls", None) or []:
        yield from _controles(hijo)
    contenido = getattr(control, "content", None)
    if isinstance(contenido, ft.Control):
        yield from _controles(contenido)


def _textos(control):
    return [elemento.value for elemento in _controles(control) if isinstance(elemento, ft.Text)]


def _boton(control, texto):
    return next(
        elemento for elemento in _controles(control)
        if isinstance(elemento, (ft.ElevatedButton, ft.OutlinedButton)) and elemento.text == texto
    )


@pytest.fixture
def usuario():
    return ResponsableCarpa("María", "carpa", "hash", "sal")


@pytest.fixture
def dashboard():
    controlador = Mock()
    controlador.alertas.return_value = [_alerta()]
    controlador.resumen.return_value = []
    controlador.contadores.return_value = {NORMAL: 0, AVISO: 0, CRITICO: 0}
    controlador.ultima_actualizacion = None
    return controlador


@pytest.mark.parametrize("clase", [JefeSanidad, ResponsableCarpa, TecnicoLogistica])
def test_panel_pide_las_alertas_con_el_usuario_para_respetar_el_filtro(clase, dashboard):
    usuario = clase("María", "maria", "hash", "sal")

    contenido = AlertasView(usuario, dashboard).construir()

    dashboard.alertas.assert_called_once_with(usuario)
    textos = _textos(contenido)
    assert "Alertas activas" in textos
    assert "Carpa de hospitalización" in textos
    assert "Temperatura" in textos
    assert "33,2 °C" in textos
    assert "Crítico" in textos
    assert "24/11/2026 18:30:00" in textos


def test_refrescar_sustituye_las_alertas_anteriores(usuario, dashboard):
    vista = AlertasView(usuario, dashboard)
    contenido = vista.construir()
    dashboard.alertas.return_value = [_alerta(sensor="Humedad", valor=65, nivel=AVISO)]

    vista.refrescar()

    assert "Humedad" in _textos(contenido)
    assert "65 °C" in _textos(contenido)
    assert "Aviso" in _textos(contenido)
    assert "Temperatura" not in _textos(contenido)


def test_sin_alertas_muestra_el_estado_vacio(usuario, dashboard):
    dashboard.alertas.return_value = []

    contenido = AlertasView(usuario, dashboard).construir()

    assert "0 activas" in _textos(contenido)
    assert any(
        isinstance(control, ft.Text) and control.value == "No hay alertas activas en tus zonas."
        and control.visible
        for control in _controles(contenido)
    )


def test_error_al_cargar_no_muestra_un_falso_estado_sin_alertas(usuario, dashboard):
    dashboard.alertas.side_effect = OSError("No se puede leer")

    contenido = AlertasView(usuario, dashboard).construir()

    assert any(
        isinstance(control, ft.Text) and control.visible
        and control.value == "No se pudieron cargar las alertas. Vuelve a intentarlo."
        for control in _controles(contenido)
    )
    assert not any(
        isinstance(control, ft.Text) and control.visible
        and control.value == "No hay alertas activas en tus zonas."
        for control in _controles(contenido)
    )


def test_inicio_conserva_el_constructor_sin_dashboard(usuario):
    zonas = Mock()
    zonas.listar.return_value = ListaEnlazada()

    contenido = InicioView(usuario, zonas).construir()

    assert "Todavía no tienes zonas asignadas." in _textos(contenido)
    assert "Alertas activas" not in _textos(contenido)


def test_inicio_inicializa_antes_de_leer_las_alertas(usuario, dashboard):
    zonas = Mock()
    zonas.listar.return_value = ListaEnlazada()
    dashboard.alertas.return_value = []
    dashboard.inicializar.side_effect = lambda: setattr(dashboard.alertas, "return_value", [_alerta()])

    contenido = InicioView(usuario, zonas, dashboard).construir()

    dashboard.inicializar.assert_called_once_with()
    assert "Temperatura" in _textos(contenido)


def test_actualizar_alertas_refresca_el_panel(usuario, dashboard):
    zonas = Mock()
    zonas.listar.return_value = ListaEnlazada()
    contenido = InicioView(usuario, zonas, dashboard).construir()
    dashboard.actualizar.side_effect = lambda: setattr(
        dashboard.alertas, "return_value", [_alerta(sensor="Humo", valor=80)]
    )

    asyncio.run(_boton(contenido, "Actualizar alertas").on_click(None))

    dashboard.actualizar.assert_called_once_with()
    assert "Humo" in _textos(contenido)
    assert "Temperatura" not in _textos(contenido)
    dashboard.alertas.assert_called_with(usuario)


def test_error_de_actualizacion_conserva_las_alertas_y_permite_reintentar(usuario, dashboard):
    zonas = Mock()
    zonas.listar.return_value = ListaEnlazada()
    contenido = InicioView(usuario, zonas, dashboard).construir()
    dashboard.actualizar.side_effect = OSError("Sin acceso al fichero")

    asyncio.run(_boton(contenido, "Actualizar alertas").on_click(None))

    assert "Temperatura" in _textos(contenido)
    error = next(
        control for control in _controles(contenido)
        if isinstance(control, ft.Text) and control.value
        == "No se pudieron actualizar las alertas. Vuelve a intentarlo."
    )
    assert error.visible
    dashboard.actualizar.side_effect = None
    dashboard.alertas.return_value = []

    asyncio.run(_boton(contenido, "Actualizar alertas").on_click(None))

    assert error.visible is False
    assert "Temperatura" not in _textos(contenido)


def test_error_de_inicializacion_conserva_las_alertas_cargadas(usuario, dashboard):
    zonas = Mock()
    zonas.listar.return_value = ListaEnlazada()
    dashboard.inicializar.side_effect = OSError("No se puede escribir")

    contenido = InicioView(usuario, zonas, dashboard).construir()

    assert "Temperatura" in _textos(contenido)
    assert any(
        isinstance(control, ft.Text) and control.visible
        and control.value == "No se pudieron actualizar las alertas. Vuelve a intentarlo."
        for control in _controles(contenido)
    )


def test_error_de_lectura_tras_actualizar_conserva_la_lista_previa(usuario, dashboard):
    zonas = Mock()
    zonas.listar.return_value = ListaEnlazada()
    contenido = InicioView(usuario, zonas, dashboard).construir()
    dashboard.alertas.side_effect = OSError("No se puede leer")

    asyncio.run(_boton(contenido, "Actualizar alertas").on_click(None))

    assert "Temperatura" in _textos(contenido)
    assert any(
        isinstance(control, ft.Text) and control.visible
        and control.value == "No se pudieron actualizar las alertas. Vuelve a intentarlo."
        for control in _controles(contenido)
    )


def test_dashboard_jefe_refresca_tambien_el_panel_de_alertas(dashboard):
    jefe = JefeSanidad("Jefe", "jefe", "hash", "sal")
    contenido = DashboardJefeView(jefe, dashboard).construir()
    dashboard.actualizar.side_effect = lambda: setattr(dashboard.alertas, "return_value", [])

    asyncio.run(_boton(contenido, "Actualizar").on_click(None))

    dashboard.actualizar.assert_called_once_with()
    dashboard.alertas.assert_called_with(jefe)
    assert "Temperatura" not in _textos(contenido)
    assert "0 activas" in _textos(contenido)


def test_dashboard_jefe_no_se_rompe_si_no_puede_leer_alertas(dashboard):
    jefe = JefeSanidad("Jefe", "jefe", "hash", "sal")
    dashboard.alertas.side_effect = OSError("No se puede leer")

    contenido = DashboardJefeView(jefe, dashboard).construir()

    assert any(
        isinstance(control, ft.Text) and control.visible
        and control.value == "No se pudieron actualizar las lecturas. Vuelve a intentarlo."
        for control in _controles(contenido)
    )
