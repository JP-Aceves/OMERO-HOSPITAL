"""Histórico de lecturas y estadísticas (HU-10). Responsable: JP (OME-70)."""
import pytest

from controller.historico_controller import MAXIMO_PUNTOS_GRAFICA, HistoricoController, leer_fecha
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorNivelDeposito, SensorTemperatura
from model.usuario import JefeSanidad, ResponsableCarpa, TecnicoLogistica
from model.zona import Zona
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas


@pytest.fixture
def historico(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    carpa = Zona("Z1", "Carpa de hospitalización", "carpa", "carpa")
    carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    zonas.anadir(carpa)
    tecnica = Zona("Z2", "Zona técnica", "zona_tecnica", "logistica")
    tecnica.anadir_sensor(SensorNivelDeposito("S6", "Depósito", 50, 20))
    zonas.anadir(tecnica)
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    lote = ListaEnlazada()
    for hora, valor in (("09:00", 26.0), ("10:00", 29.0), ("11:00", 33.0), ("12:00", 24.0)):
        lote.insertar(Lectura("Z1", "S1", "temperatura", valor, "°C", f"2026-11-23T{hora}:00"))
    lote.insertar(Lectura("Z2", "S6", "nivel_deposito", 45.0, "%", "2026-11-23T10:00:00"))
    lecturas.anadir(lote)
    return HistoricoController(zonas, lecturas)


jefe = JefeSanidad("Elena", "jefe", "hash", "sal")
carpa = ResponsableCarpa("María", "carpa", "hash", "sal")
tecnico = TecnicoLogistica("Luis", "logistica", "hash", "sal")


def test_cada_rol_solo_ve_sus_zonas(historico):
    assert [z["id"] for z in historico.zonas(jefe)] == ["Z1", "Z2"]
    assert [z["id"] for z in historico.zonas(carpa)] == ["Z1"]
    assert [z["id"] for z in historico.zonas(tecnico)] == ["Z2"]


def test_sensores_de_una_zona(historico):
    assert historico.sensores(jefe, "Z1") == [
        {"id": "S1", "nombre": "Temperatura", "tipo": "temperatura", "unidad": "°C"}]
    assert historico.sensores(carpa, "Z2") == []


def test_consulta_sin_fechas_da_todas_las_lecturas_y_sus_estadisticas(historico):
    datos = historico.consultar(jefe, "Z1", "S1")

    assert datos["total"] == 4
    assert datos["media"] == 28.0
    assert datos["maximo"] == {"fecha_hora": "2026-11-23T11:00:00", "valor": 33.0, "estado": "critico"}
    assert datos["minimo"]["valor"] == 24.0
    assert [l["estado"] for l in datos["lecturas"]] == ["normal", "aviso", "critico", "normal"]
    assert (datos["umbral_aviso"], datos["umbral_critico"], datos["unidad"]) == (28, 32, "°C")
    assert datos["grafica"] == datos["lecturas"]


def test_filtrar_por_fechas(historico):
    datos = historico.consultar(jefe, "Z1", "S1", "23/11/2026 10:00", "23/11/2026 11:00")

    assert [l["valor"] for l in datos["lecturas"]] == [29.0, 33.0]
    assert datos["media"] == 31.0


def test_una_fecha_sin_hora_cuenta_el_dia_entero(historico):
    assert historico.consultar(jefe, "Z1", "S1", "", "23/11/2026")["total"] == 4
    assert historico.consultar(jefe, "Z1", "S1", "24/11/2026", "")["total"] == 0


def test_periodo_sin_lecturas(historico):
    datos = historico.consultar(jefe, "Z1", "S1", "01/01/2026", "02/01/2026")

    assert (datos["total"], datos["media"], datos["maximo"], datos["minimo"]) == (0, None, None, None)


@pytest.mark.parametrize("zona, sensor, desde, hasta, error", [
    ("", "S1", "", "", "Elige una zona"),
    ("Z1", "", "", "", "Elige un sensor"),
    ("Z1", "S6", "", "", "Ese sensor no es de la zona elegida"),
    ("Z1", "S1", "ayer", "", "La fecha «Desde» debe tener el formato dd/mm/aaaa hh:mm"),
    ("Z1", "S1", "", "32/11/2026", "La fecha «Hasta» debe tener el formato dd/mm/aaaa hh:mm"),
    ("Z1", "S1", "24/11/2026", "23/11/2026", "La fecha «Desde» no puede ser posterior a «Hasta»"),
])
def test_errores_del_filtro(historico, zona, sensor, desde, hasta, error):
    assert historico.consultar(jefe, zona, sensor, desde, hasta) == error


def test_no_se_puede_consultar_una_zona_ajena(historico):
    assert historico.consultar(carpa, "Z2", "S6") == "No tienes acceso a esa zona"


def test_la_grafica_se_reduce_si_hay_muchas_lecturas(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    zona = Zona("Z1", "Carpa", "carpa")
    zona.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    zonas.anadir(zona)
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    lote = ListaEnlazada()
    for minuto in range(1000):
        lote.insertar(Lectura("Z1", "S1", "temperatura", 20 + minuto % 10, "°C",
                              f"2026-11-{1 + minuto // 1440:02d}T{minuto // 60 % 24:02d}:{minuto % 60:02d}:00"))
    lecturas.anadir(lote)

    datos = HistoricoController(zonas, lecturas).consultar(jefe, "Z1", "S1")

    assert datos["total"] == 1000
    assert len(datos["grafica"]) == MAXIMO_PUNTOS_GRAFICA
    assert datos["grafica"][-1] == datos["lecturas"][-1]


def test_leer_fecha():
    assert leer_fecha("23/11/2026 18:30").hour == 18
    assert leer_fecha("23/11/2026", fin_del_dia=True).hour == 23
    assert leer_fecha("2026-11-23") is None
