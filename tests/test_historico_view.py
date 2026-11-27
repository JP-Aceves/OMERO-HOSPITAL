"""Pantalla "Histórico y estadísticas" (mockup 07). Responsable: JP (OME-70)."""
from types import SimpleNamespace

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
from datetime import datetime

from view.historico_view import HistoricoView, escala_eje_y, fecha_corta, leer_dia, numero


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
    assert leer_dia("23/11/2026") == datetime(2026, 11, 23)
    assert leer_dia("") is None and leer_dia("mañana") is None


# ---------- OME-71 ----------

def test_cambiar_de_sensor_cambia_estadisticas_grafica_y_tabla(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    contenido = vista.construir()

    vista.campo_sensor.value = "S2"
    vista.campo_sensor.on_change(None)

    assert _por_clave(contenido, "historico_media").value == "55,0 %"
    assert _por_clave(contenido, "historico_total").value == "1"
    assert "Humedad · Carpa de hospitalización" in _textos(contenido)
    assert [p.y for p in vista.grafica.data_series[2].data_points] == [55.0]
    assert len(vista.tabla.rows) == 1


def test_las_fechas_se_eligen_en_el_calendario(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    contenido = vista.construir()

    assert vista.campo_desde.read_only and vista.campo_hasta.read_only
    assert isinstance(vista.calendario_desde, ft.DatePicker)
    vista.calendario_desde.on_change(SimpleNamespace(control=SimpleNamespace(value=datetime(2026, 11, 24))))

    assert vista.campo_desde.value == "24/11/2026"
    assert _por_clave(contenido, "historico_vacio")

    vista.calendario_hasta.on_change(SimpleNamespace(control=SimpleNamespace(value=datetime(2026, 11, 23))))
    assert vista.error.visible and "posterior" in vista.error.value


def test_quitar_fechas_vuelve_a_todas_las_lecturas(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    contenido = vista.construir()
    vista.campo_desde.value = "24/11/2026"
    vista._aplicar()

    _por_clave(contenido, "historico_quitar").on_click(None)

    assert vista.campo_desde.value == "" and vista.campo_hasta.value == ""
    assert _por_clave(contenido, "historico_total").value == "3"


def test_refrescar_enseña_las_lecturas_nuevas_y_no_repinta_si_no_hay(controlador):
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    contenido = vista.construir()

    antes = list(vista.resultado.controls)
    vista.refrescar()
    assert vista.resultado.controls == antes  # sin lecturas nuevas, la gráfica no parpadea

    nueva = ListaEnlazada()
    nueva.insertar(Lectura("Z1", "S1", "temperatura", 20.0, "°C", "2026-11-23T12:00:00"))
    controlador.repo_lecturas.anadir(nueva)
    vista.refrescar()

    assert _por_clave(contenido, "historico_total").value == "4"
    assert _por_clave(contenido, "historico_minimo").value == "20,0 °C"


def test_el_eje_y_usa_limites_redondos():
    assert escala_eje_y(16.1, 46.1) == (10, 50, 10)  # antes salían 16,1 y 46,1 encima de 20 y 45
    assert escala_eje_y(18.0, 32.0) == (15, 35, 5)
    for bajo, alto in ((0.0, 0.0), (19.3, 20.0), (-3.2, 104.7)):
        minimo, maximo, paso = escala_eje_y(bajo, alto)
        assert minimo <= bajo and alto <= maximo and minimo < maximo and paso > 0
        for limite in (minimo, maximo):
            assert limite / paso == pytest.approx(round(limite / paso))


def test_abrir_el_calendario_marca_el_dia_del_campo(controlador):
    abiertos = []
    vista = HistoricoView(JefeSanidad("Elena", "jefe", "hash", "sal"), controlador)
    contenido = vista.construir()
    contenido._Control__page = SimpleNamespace(open=abiertos.append)  # página falsa: solo apunta qué se abre

    vista.campo_desde.value = "23/11/2026"
    vista.campo_desde.on_click(None)

    assert abiertos == [vista.calendario_desde]
    assert vista.calendario_desde.value == datetime(2026, 11, 23)
    assert vista.calendario_desde.value <= vista.calendario_desde.last_date
