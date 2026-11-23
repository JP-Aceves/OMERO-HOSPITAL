"""Pantalla "Histórico y estadísticas" (mockup 07). Responsable: JP (OME-70)."""
import flet as ft
import pytest

from controller.historico_controller import HistoricoController
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorHumedad, SensorTemperatura
from model.usuario import JefeSanidad, ResponsableCarpa
from model.zona import Zona
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from view.historico_view import HistoricoView, fecha_corta, numero


def _controles(control):
    yield control
    for hijo in getattr(control, "controls", None) or []:
        yield from _controles(hijo)
    contenido = getattr(control, "content", None)
    if isinstance(contenido, ft.Control):
        yield from _controles(contenido)
    for fila in getattr(control, "rows", None) or []:
        for celda in fila.cells:
            yield from _controles(celda.content)


def _por_clave(control, clave):
    return next(elemento for elemento in _controles(control) if elemento.key == clave)


def _textos(control):
    return [e.value for e in _controles(control) if isinstance(e, ft.Text)]


@pytest.fixture
def controlador(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    carpa = Zona("Z1", "Carpa de hospitalización", "carpa", "carpa")
    carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    carpa.anadir_sensor(SensorHumedad("S2", "Humedad", 60, 70))
    zonas.anadir(carpa)
    zonas.anadir(Zona("Z3", "Exterior", "exterior"))
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    lote = ListaEnlazada()
    for hora, valor in (("09:00", 26.0), ("10:00", 29.0), ("11:00", 33.0)):
        lote.insertar(Lectura("Z1", "S1", "temperatura", valor, "°C", f"2026-11-23T{hora}:00"))
    lote.insertar(Lectura("Z1", "S2", "humedad", 55.0, "%", "2026-11-23T10:00:00"))
    lecturas.anadir(lote)
    return HistoricoController(zonas, lecturas)


def test_al_abrir_muestra_la_primera_zona_y_su_primer_sensor(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    contenido = vista.construir()

    assert vista.campo_zona.value == "Z1"
    assert [o.key for o in vista.campo_zona.options] == ["Z1", "Z3"]
    assert vista.campo_sensor.value == "S1"
    assert _por_clave(contenido, "historico_media").value == "29,3 °C"
    assert _por_clave(contenido, "historico_maximo").value == "33,0 °C"
    assert _por_clave(contenido, "historico_minimo").value == "26,0 °C"
    assert _por_clave(contenido, "historico_total").value == "3"
    assert "Temperatura · Carpa de hospitalización" in _textos(contenido)


def test_la_grafica_lleva_las_lineas_de_aviso_y_critico(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    vista.construir()
    grafica = vista.grafica

    critico, aviso, serie = grafica.data_series
    assert {p.y for p in critico.data_points} == {32}
    assert {p.y for p in aviso.data_points} == {28}
    assert [p.y for p in serie.data_points] == [26.0, 29.0, 33.0]
    assert len(grafica.bottom_axis.labels) == 3


def test_la_tabla_enseña_las_ultimas_lecturas_con_su_nivel(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    vista.construir()
    tabla = vista.tabla

    assert len(tabla.rows) == 3
    primera = _textos(tabla.rows[0].cells[0].content)[0], _textos(tabla.rows[0].cells[2].content)[0]
    assert primera == ("23/11 11:00", "Crítico")


def test_cambiar_de_zona_recarga_los_sensores(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    vista.construir()

    vista.campo_zona.value = "Z3"
    vista._al_cambiar_zona()

    assert vista.campo_sensor.options == []
    assert vista.error.visible and vista.error.value == "Elige un sensor"


def test_filtrar_por_fechas_y_periodo_vacio(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    contenido = vista.construir()

    vista.campo_desde.value = "23/11/2026 10:00"
    vista._aplicar()
    assert _por_clave(contenido, "historico_total").value == "2"

    vista.campo_desde.value = "24/11/2026"
    vista._aplicar()
    assert _por_clave(contenido, "historico_vacio")


def test_una_fecha_mal_escrita_enseña_el_error(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    vista.construir()

    vista.campo_hasta.value = "mañana"
    vista._aplicar()

    assert vista.error.visible
    assert "Hasta" in vista.error.value


def test_un_usuario_sin_zonas_ve_un_aviso(controlador, tmp_path):
    vacio = HistoricoController(RepositorioZonas(tmp_path / "otra.json"), RepositorioLecturas(tmp_path / "l2.json"))
    contenido = HistoricoView(ResponsableCarpa("María", "carpa", "hash", "sal"), vacio).construir()

    assert "Todavía no tienes zonas asignadas." in _textos(contenido)


def test_formatos():
    assert numero(31.44) == "31,4"
    assert fecha_corta("2026-11-23T18:30:00") == "23/11 18:30"
