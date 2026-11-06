"""Pruebas del repositorio de zonas (OME-34), con las clases reales de OME-31."""
import json
from pathlib import Path

import pytest

from model.actuador import Actuador
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorTemperatura
from model.zona import Zona
from persistence.repositorio_zonas import RepositorioZonas

ZONAS_DE_PRUEBA = Path(__file__).resolve().parent.parent / "data" / "zonas.json"


def nueva_zona(id_zona, responsable=None, sensores=(), actuadores=()):
    zona = Zona(id_zona, f"Zona {id_zona}", "carpa", responsable)
    for id_sensor in sensores:
        zona.anadir_sensor(SensorTemperatura(id_sensor, "DHT22 temperatura", 28, 32))
    for id_actuador in actuadores:
        zona.anadir_actuador(Actuador(id_actuador, "Ventilador", "ventilador"))
    return zona


def ids(zonas):
    return ",".join(zona.id for zona in zonas)


def test_sin_fichero_no_hay_zonas(tmp_path):
    repositorio = RepositorioZonas(tmp_path / "zonas.json")

    zonas = repositorio.listar()

    assert isinstance(zonas, ListaEnlazada)
    assert len(zonas) == 0


def test_una_zona_anadida_sigue_ahi_al_recargar_con_sensores_y_actuadores(tmp_path):
    # Es el "Está terminada cuando" de la issue: crear, cerrar y volver a cargar.
    ruta = tmp_path / "zonas.json"
    RepositorioZonas(ruta).anadir(nueva_zona("Z1", "carpa", ["S1", "S2"], ["A1"]))

    zona = RepositorioZonas(ruta).buscar("Z1")

    assert zona.responsable == "carpa"
    assert len(zona.sensores) == 2
    assert len(zona.actuadores) == 1
    assert isinstance(zona.buscar_sensor("S2"), SensorTemperatura)


def test_las_zonas_se_recargan_en_el_mismo_orden(tmp_path):
    ruta = tmp_path / "zonas.json"
    repositorio = RepositorioZonas(ruta)
    for id_zona in ("Z1", "Z2", "Z3"):
        repositorio.anadir(nueva_zona(id_zona))

    assert ids(RepositorioZonas(ruta).listar()) == "Z1,Z2,Z3"


def test_guardar_deja_el_zonas_json_de_prueba_igual(tmp_path):
    ruta = tmp_path / "zonas.json"
    ruta.write_text(ZONAS_DE_PRUEBA.read_text(encoding="utf-8"), encoding="utf-8")

    RepositorioZonas(ruta).guardar()

    # rstrip("\n") quita el salto de línea del final, por si el archivo lo tiene.
    guardado = ruta.read_text(encoding="utf-8").rstrip("\n")
    original = ZONAS_DE_PRUEBA.read_text(encoding="utf-8").rstrip("\n")
    assert guardado == original


def test_guardar_crea_la_carpeta_si_no_existe(tmp_path):
    ruta = tmp_path / "data" / "zonas.json"

    RepositorioZonas(ruta).guardar()

    assert json.loads(ruta.read_text(encoding="utf-8")) == []


def test_buscar_por_id(tmp_path):
    repositorio = RepositorioZonas(tmp_path / "zonas.json")
    repositorio.anadir(nueva_zona("Z1"))

    assert repositorio.buscar("Z1").id == "Z1"
    assert repositorio.buscar("Z9") is None


def test_anadir_un_id_repetido_lanza_value_error(tmp_path):
    ruta = tmp_path / "zonas.json"
    repositorio = RepositorioZonas(ruta)
    repositorio.anadir(nueva_zona("Z1"))

    with pytest.raises(ValueError):
        repositorio.anadir(nueva_zona("Z1"))

    assert len(RepositorioZonas(ruta).listar()) == 1


def test_actualizar_sustituye_la_zona_y_mantiene_el_orden(tmp_path):
    ruta = tmp_path / "zonas.json"
    repositorio = RepositorioZonas(ruta)
    repositorio.anadir(nueva_zona("Z1"))
    repositorio.anadir(nueva_zona("Z2"))
    cambiada = nueva_zona("Z1", "carpa", ["S1"])
    cambiada.nombre = "Carpa nueva"

    repositorio.actualizar(cambiada)

    recargado = RepositorioZonas(ruta)
    assert ids(recargado.listar()) == "Z1,Z2"
    assert recargado.buscar("Z1").nombre == "Carpa nueva"
    assert recargado.buscar("Z1").responsable == "carpa"
    assert len(recargado.buscar("Z1").sensores) == 1


def test_actualizar_una_zona_que_no_existe_lanza_value_error(tmp_path):
    repositorio = RepositorioZonas(tmp_path / "zonas.json")

    with pytest.raises(ValueError):
        repositorio.actualizar(nueva_zona("Z9"))


def test_eliminar_borra_la_zona_y_lo_guarda(tmp_path):
    ruta = tmp_path / "zonas.json"
    repositorio = RepositorioZonas(ruta)
    repositorio.anadir(nueva_zona("Z1"))
    repositorio.anadir(nueva_zona("Z2"))

    assert repositorio.eliminar("Z1") is True
    assert repositorio.eliminar("Z9") is False
    assert ids(RepositorioZonas(ruta).listar()) == "Z2"


def test_zonas_de_devuelve_solo_las_de_ese_responsable():
    repositorio = RepositorioZonas(ZONAS_DE_PRUEBA)

    assert isinstance(repositorio.zonas_de("carpa"), ListaEnlazada)
    assert ids(repositorio.zonas_de("carpa")) == "Z1"
    assert ids(repositorio.zonas_de("logistica")) == "Z2,Z3"
    assert len(repositorio.zonas_de("jefe")) == 0


def test_siguiente_id_con_las_zonas_de_prueba():
    repositorio = RepositorioZonas(ZONAS_DE_PRUEBA)

    assert repositorio.siguiente_id("Z") == "Z4"
    assert repositorio.siguiente_id("S") == "S8"
    assert repositorio.siguiente_id("A") == "A4"


def test_siguiente_id_sin_zonas_empieza_en_1(tmp_path):
    repositorio = RepositorioZonas(tmp_path / "zonas.json")

    assert repositorio.siguiente_id("Z") == "Z1"
    assert repositorio.siguiente_id("S") == "S1"


def test_el_zonas_json_de_prueba_tiene_3_zonas_7_sensores_y_3_actuadores():
    zonas = RepositorioZonas(ZONAS_DE_PRUEBA).listar()

    assert ids(zonas) == "Z1,Z2,Z3"
    assert sum(len(zona.sensores) for zona in zonas) == 7
    assert sum(len(zona.actuadores) for zona in zonas) == 3