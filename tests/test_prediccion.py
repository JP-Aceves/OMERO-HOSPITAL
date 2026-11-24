"""Pruebas de la predicción del vaciado del depósito (OME-65)."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.prediccion import MINIMO_LECTURAS, predecir_vaciado, recta, ultimo_tramo
from service.simulador import Simulador

ZONAS_DE_PRUEBA = Path(__file__).resolve().parent.parent / "data" / "zonas.json"
INICIO = datetime(2026, 11, 24, 10, 0)


def lecturas_del_deposito(valores, minutos_entre=10):
    """Lecturas inventadas del HC-SR04 (S6), una cada minutos_entre minutos desde INICIO."""
    lecturas = ListaEnlazada()
    for i, valor in enumerate(valores):
        momento = INICIO + timedelta(minutes=i * minutos_entre)
        lecturas.insertar(Lectura("Z2", "S6", "nivel_deposito", valor, "%", momento.isoformat()))
    return lecturas


# ---------- recta ----------

def test_recta_de_una_bajada_constante():
    a, b = recta(lecturas_del_deposito([100, 98, 96, 94, 92]))

    assert a == pytest.approx(100)
    assert b == pytest.approx(-0.2)  # 2 puntos cada 10 minutos


def test_recta_con_puntos_que_no_estan_alineados_usa_minimos_cuadrados():
    # t = 0, 1, 2, 3 · y = 1, 3, 2, 4. A mano: b = (4·19 - 6·10) / (4·14 - 6²) = 0,8 y a = (10 - 0,8·6) / 4 = 1,3
    a, b = recta(lecturas_del_deposito([1, 3, 2, 4], minutos_entre=1))

    assert a == pytest.approx(1.3)
    assert b == pytest.approx(0.8)


def test_recta_sin_dos_horas_distintas_da_error():
    with pytest.raises(ValueError):
        recta(lecturas_del_deposito([80]))
    with pytest.raises(ValueError):
        recta(lecturas_del_deposito([80, 79, 78], minutos_entre=0))


# ---------- predecir_vaciado ----------

def test_bajada_constante_predice_la_hora_de_vaciado():
    # Baja 0,2 % por minuto desde 100 %: llega a 0 a los 500 minutos.
    vaciado = predecir_vaciado(lecturas_del_deposito([100, 98, 96, 94, 92]))

    assert vaciado == INICIO + timedelta(minutes=500)


def test_nivel_estable_no_predice():
    assert predecir_vaciado(lecturas_del_deposito([60, 60, 60, 60, 60, 60])) is None


def test_nivel_que_sube_no_predice():
    assert predecir_vaciado(lecturas_del_deposito([40, 42, 44, 46, 48])) is None


@pytest.mark.parametrize("cuantas", range(MINIMO_LECTURAS))
def test_con_menos_de_cinco_lecturas_no_predice(cuantas):
    assert predecir_vaciado(lecturas_del_deposito([90 - i for i in range(cuantas)])) is None


def test_lecturas_a_la_misma_hora_no_predice():
    assert predecir_vaciado(lecturas_del_deposito([90, 89, 88, 87, 86], minutos_entre=0)) is None


# ---------- último tramo (rellenados) ----------

def test_solo_usa_las_lecturas_desde_el_ultimo_rellenado():
    # Baja hasta el 12 %, se rellena al 95 % (minuto 30) y vuelve a bajar 0,2 % por minuto.
    lecturas = lecturas_del_deposito([30, 20, 12, 95, 93, 91, 89, 87])

    assert ",".join(str(lectura.valor) for lectura in ultimo_tramo(lecturas)) == "95,93,91,89,87"
    # Desde el rellenado: 95 / 0,2 = 475 minutos.
    assert predecir_vaciado(lecturas) == INICIO + timedelta(minutes=30 + 475)


def test_justo_despues_de_rellenar_no_predice_hasta_tener_cinco_lecturas():
    lecturas = lecturas_del_deposito([80, 70, 60, 50, 40, 95, 94])

    assert predecir_vaciado(lecturas) is None


def test_una_subida_pequena_no_cuenta_como_rellenado():
    # Ruido del sensor: sube 1 punto, pero el depósito sigue bajando.
    lecturas = lecturas_del_deposito([100, 98, 99, 96, 94, 92])

    assert len(ultimo_tramo(lecturas)) == 6
    assert predecir_vaciado(lecturas) is not None


# ---------- con el simulador (criterio de la issue) ----------

def test_con_50_rondas_del_simulador_la_prediccion_es_coherente(tmp_path):
    repo_lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    Simulador(RepositorioZonas(ZONAS_DE_PRUEBA), repo_lecturas, semilla=1).generar(50, 5)

    lecturas = RepositorioLecturas(tmp_path / "lecturas.json").de_sensor("S6")
    tramo = ultimo_tramo(lecturas)
    a, b = recta(tramo)
    vaciado = predecir_vaciado(lecturas)
    ultima = datetime.fromisoformat(repo_lecturas.ultima("S6").fecha_hora)

    assert len(lecturas) == 50
    # El simulador baja el depósito entre 0,5 y 2 puntos cada 5 minutos: de 0,1 a 0,4 % por minuto.
    assert 0.1 <= -b <= 0.4
    assert vaciado is not None and vaciado > ultima