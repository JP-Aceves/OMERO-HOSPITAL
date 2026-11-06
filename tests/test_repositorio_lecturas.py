"""Pruebas del repositorio de lecturas (OME-34)."""
import json

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from persistence.repositorio_lecturas import RepositorioLecturas


def lectura(sensor, valor, hora):
    return Lectura("Z1", sensor, "temperatura", valor, "°C", f"2026-11-10T{hora}:00")


def lista_de(*lecturas):
    resultado = ListaEnlazada()
    for una in lecturas:
        resultado.insertar(una)
    return resultado


def valores(lecturas):
    return ",".join(str(una.valor) for una in lecturas)


def test_sin_fichero_no_hay_lecturas(tmp_path):
    repositorio = RepositorioLecturas(tmp_path / "lecturas.json")

    assert isinstance(repositorio.de_sensor("S1"), ListaEnlazada)
    assert len(repositorio.de_sensor("S1")) == 0
    assert repositorio.ultima("S1") is None


def test_las_lecturas_siguen_ahi_al_recargar(tmp_path):
    ruta = tmp_path / "lecturas.json"
    RepositorioLecturas(ruta).anadir(lista_de(lectura("S1", 25.0, "18:00"), lectura("S1", 26.5, "18:05")))

    recargado = RepositorioLecturas(ruta)

    assert valores(recargado.de_sensor("S1")) == "25.0,26.5"


def test_anadir_va_al_final_y_no_borra_lo_anterior(tmp_path):
    ruta = tmp_path / "lecturas.json"
    RepositorioLecturas(ruta).anadir(lista_de(lectura("S1", 25.0, "18:00")))
    RepositorioLecturas(ruta).anadir(lista_de(lectura("S1", 27.0, "18:05")))

    assert valores(RepositorioLecturas(ruta).de_sensor("S1")) == "25.0,27.0"


def test_de_sensor_solo_devuelve_las_de_ese_sensor(tmp_path):
    repositorio = RepositorioLecturas(tmp_path / "lecturas.json")
    repositorio.anadir(lista_de(lectura("S1", 25.0, "18:00"), lectura("S2", 60.0, "18:00"),
                                lectura("S1", 26.0, "18:05")))

    assert valores(repositorio.de_sensor("S1")) == "25.0,26.0"
    assert valores(repositorio.de_sensor("S2")) == "60.0"
    assert len(repositorio.de_sensor("S9")) == 0


def test_ultima_es_la_mas_reciente_de_ese_sensor(tmp_path):
    repositorio = RepositorioLecturas(tmp_path / "lecturas.json")
    repositorio.anadir(lista_de(lectura("S1", 25.0, "18:00"), lectura("S1", 26.0, "18:05"),
                                lectura("S2", 60.0, "18:10")))

    assert repositorio.ultima("S1").valor == 26.0
    assert repositorio.ultima("S1").fecha_hora == "2026-11-10T18:05:00"
    assert repositorio.ultima("S9") is None


def test_el_json_tiene_el_formato_del_readme(tmp_path):
    ruta = tmp_path / "data" / "lecturas.json"

    RepositorioLecturas(ruta).anadir(lista_de(lectura("S1", 31.4, "18:30")))

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos == [{"zona": "Z1", "sensor": "S1", "tipo": "temperatura", "valor": 31.4,
                      "unidad": "°C", "fecha_hora": "2026-11-10T18:30:00"}]