"""Pruebas del repositorio de zonas (OME-34).

Mientras no esté OME-31, Zona y crear_zona están vacías. Por eso estas
pruebas usan una zona de prueba con lo único que el repositorio necesita:
id, responsable, sensores, actuadores y to_dict().
"""
import json
from pathlib import Path

import pytest

import persistence.repositorio_zonas
from model.lista_enlazada import ListaEnlazada
from persistence.repositorio_zonas import RepositorioZonas

ZONAS_DE_PRUEBA = Path(__file__).resolve().parent.parent / "data" / "zonas.json"


class Pieza:
    """Sensor o actuador de prueba: al repositorio solo le importa su id."""

    def __init__(self, datos):
        self.id = datos["id"]


class ZonaDePrueba:
    """Imita a la Zona de OME-31 a partir de su diccionario."""

    def __init__(self, datos):
        self.datos = datos
        self.id = datos["id"]
        self.responsable = datos["responsable"]
        self.sensores = ListaEnlazada()
        for sensor in datos["sensores"]:
            self.sensores.insertar(Pieza(sensor))
        self.actuadores = ListaEnlazada()
        for actuador in datos["actuadores"]:
            self.actuadores.insertar(Pieza(actuador))

    def to_dict(self):
        return self.datos


@pytest.fixture(autouse=True)
def usar_zonas_de_prueba(monkeypatch):
    # Al leer el JSON, el repositorio llamará a ZonaDePrueba en vez de a crear_zona.
    monkeypatch.setattr(persistence.repositorio_zonas, "crear_zona", ZonaDePrueba)


def datos_zona(id_zona, responsable=None, sensores=(), actuadores=()):
    return {
        "id": id_zona,
        "nombre": f"Zona {id_zona}",
        "tipo": "carpa",
        "responsable": responsable,
        "sensores": [{"id": id_sensor} for id_sensor in sensores],
        "actuadores": [{"id": id_actuador} for id_actuador in actuadores],
    }


def escribir(ruta, *zonas):
    ruta.write_text(json.dumps(zonas, ensure_ascii=False, indent=2), encoding="utf-8")


def ids(zonas):
    return ",".join(zona.id for zona in zonas)


def test_sin_fichero_no_hay_zonas(tmp_path):
    repositorio = RepositorioZonas(tmp_path / "zonas.json")

    zonas = repositorio.listar()

    assert isinstance(zonas, ListaEnlazada)
    assert len(zonas) == 0


def test_carga_las_zonas_en_el_orden_del_fichero(tmp_path):
    ruta = tmp_path / "zonas.json"
    escribir(ruta, datos_zona("Z1"), datos_zona("Z2"), datos_zona("Z3"))

    repositorio = RepositorioZonas(ruta)

    assert ids(repositorio.listar()) == "Z1,Z2,Z3"


def test_guardar_deja_el_fichero_igual_que_lo_leyo(tmp_path):
    ruta = tmp_path / "zonas.json"
    escribir(ruta, datos_zona("Z1", "carpa", ["S1", "S2"], ["A1"]), datos_zona("Z2"))
    antes = ruta.read_text(encoding="utf-8")

    RepositorioZonas(ruta).guardar()

    assert ruta.read_text(encoding="utf-8") == antes


def test_guardar_crea_la_carpeta_si_no_existe(tmp_path):
    ruta = tmp_path / "data" / "zonas.json"

    RepositorioZonas(ruta).guardar()

    assert json.loads(ruta.read_text(encoding="utf-8")) == []


def test_buscar_por_id(tmp_path):
    ruta = tmp_path / "zonas.json"
    escribir(ruta, datos_zona("Z1"), datos_zona("Z2"))
    repositorio = RepositorioZonas(ruta)

    assert repositorio.buscar("Z2").id == "Z2"
    assert repositorio.buscar("Z9") is None


def test_el_zonas_json_de_prueba_tiene_3_zonas_7_sensores_y_3_actuadores():
    repositorio = RepositorioZonas(ZONAS_DE_PRUEBA)
    zonas = repositorio.listar()

    assert ids(zonas) == "Z1,Z2,Z3"
    assert sum(len(zona.sensores) for zona in zonas) == 7
    assert sum(len(zona.actuadores) for zona in zonas) == 3
    assert repositorio.buscar("Z1").responsable == "carpa"
    assert repositorio.buscar("Z2").responsable == "logistica"
    assert repositorio.buscar("Z3").responsable == "logistica"