"""Pruebas del simulador de lecturas (OME-33)."""
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service import simulador
from service.simulador import Simulador

ZONAS_DE_PRUEBA = Path(__file__).resolve().parent.parent / "data" / "zonas.json"


def nuevo_simulador(ruta_lecturas, semilla=1):
    return Simulador(RepositorioZonas(ZONAS_DE_PRUEBA), RepositorioLecturas(ruta_lecturas), semilla)


def sensores_de_prueba():
    for zona in RepositorioZonas(ZONAS_DE_PRUEBA).listar():
        for sensor in zona.sensores:
            yield sensor


def valores(lecturas):
    return ",".join(str(lectura.valor) for lectura in lecturas)


def test_una_ronda_tiene_una_lectura_por_sensor_y_se_guarda(tmp_path):
    ruta = tmp_path / "lecturas.json"

    ronda = nuevo_simulador(ruta).generar_ronda()

    assert isinstance(ronda, ListaEnlazada)
    assert ",".join(lectura.sensor for lectura in ronda) == "S1,S2,S3,S4,S5,S6,S7"
    assert len(RepositorioLecturas(ruta).de_sensor("S1")) == 1


def test_cada_lectura_lleva_la_zona_el_tipo_y_la_unidad_de_su_sensor(tmp_path):
    ronda = nuevo_simulador(tmp_path / "lecturas.json").generar_ronda()

    temperatura = ronda.buscar(lambda lectura: lectura.sensor == "S1")
    viento = ronda.buscar(lambda lectura: lectura.sensor == "S7")

    assert (temperatura.zona, temperatura.tipo, temperatura.unidad) == ("Z1", "temperatura", "°C")
    assert (viento.zona, viento.tipo, viento.unidad) == ("Z3", "viento", "km/h")
    datetime.fromisoformat(temperatura.fecha_hora)  # si el formato no es ISO, esto falla


def test_el_json_tiene_el_formato_del_readme(tmp_path):
    ruta = tmp_path / "lecturas.json"

    nuevo_simulador(ruta).generar_ronda()

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert set(datos[0]) == {"zona", "sensor", "tipo", "valor", "unidad", "fecha_hora"}


def test_los_valores_siempre_estan_dentro_del_rango(tmp_path):
    ruta = tmp_path / "lecturas.json"

    nuevo_simulador(ruta).generar(150)

    lecturas = RepositorioLecturas(ruta)
    for sensor in sensores_de_prueba():
        minimo, maximo = sensor.RANGO
        for lectura in lecturas.de_sensor(sensor.id):
            assert minimo <= lectura.valor <= maximo


def test_fuera_de_los_picos_la_variacion_es_suave(tmp_path):
    ruta = tmp_path / "lecturas.json"
    nuevo_simulador(ruta).generar(150)

    anterior = None
    for lectura in RepositorioLecturas(ruta).de_sensor("S1"):
        sin_picos = anterior is not None and anterior < 32 and lectura.valor < 32
        if sin_picos:
            assert abs(lectura.valor - anterior) < 6  # menos del 20 % del rango (15 a 45 °C)
        anterior = lectura.valor


def test_el_deposito_solo_baja_salvo_cuando_se_rellena(tmp_path):
    ruta = tmp_path / "lecturas.json"
    nuevo_simulador(ruta).generar(150)

    anterior = None
    rellenos = 0
    for lectura in RepositorioLecturas(ruta).de_sensor("S6"):
        if anterior is not None and lectura.valor > anterior:
            rellenos += 1
            assert lectura.valor >= 90
        elif anterior is not None:
            assert lectura.valor < anterior
        anterior = lectura.valor
    assert rellenos >= 1  # en 150 rondas le da tiempo a vaciarse y rellenarse


def test_el_deposito_se_rellena_al_bajar_del_10(tmp_path):
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    casi_vacio = ListaEnlazada()
    casi_vacio.insertar(Lectura("Z2", "S6", "nivel_deposito", 10.4, "%", "2026-11-12T10:00:00"))
    lecturas.anadir(casi_vacio)

    ronda = Simulador(RepositorioZonas(ZONAS_DE_PRUEBA), lecturas, semilla=1).generar_ronda()

    assert ronda.buscar(lambda lectura: lectura.sensor == "S6").valor >= 90


def test_hay_picos_mas_alla_del_umbral_critico(tmp_path):
    ruta = tmp_path / "lecturas.json"
    nuevo_simulador(ruta).generar(200)
    lecturas = RepositorioLecturas(ruta)

    picos_temperatura = sum(1 for lectura in lecturas.de_sensor("S1") if lectura.valor >= 32)
    cortes_de_luz = sum(1 for lectura in lecturas.de_sensor("S4") if lectura.valor <= 20)

    assert 2 <= picos_temperatura <= 30  # alrededor del 5 % de 200
    assert 2 <= cortes_de_luz <= 30      # en la luz, el pico es hacia abajo (INVERSO)


def test_con_la_misma_semilla_salen_los_mismos_valores(tmp_path):
    nuevo_simulador(tmp_path / "a.json", semilla=7).generar(20)
    nuevo_simulador(tmp_path / "b.json", semilla=7).generar(20)
    nuevo_simulador(tmp_path / "c.json", semilla=8).generar(20)

    a = RepositorioLecturas(tmp_path / "a.json")
    b = RepositorioLecturas(tmp_path / "b.json")
    c = RepositorioLecturas(tmp_path / "c.json")
    for sensor in sensores_de_prueba():
        assert valores(a.de_sensor(sensor.id)) == valores(b.de_sensor(sensor.id))
    assert valores(a.de_sensor("S1")) != valores(c.de_sensor("S1"))


def test_generar_crea_el_historico_con_fechas_separadas(tmp_path):
    ruta = tmp_path / "lecturas.json"

    nuevo_simulador(ruta).generar(10, minutos_entre=5)

    lecturas = RepositorioLecturas(ruta)
    temperaturas = lecturas.de_sensor("S1")
    primera = datetime.fromisoformat(temperaturas.cabeza.dato.fecha_hora)
    segunda = datetime.fromisoformat(temperaturas.cabeza.siguiente.dato.fecha_hora)
    ultima = datetime.fromisoformat(lecturas.ultima("S1").fecha_hora)
    assert len(temperaturas) == 10
    assert segunda - primera == timedelta(minutes=5)
    assert ultima - primera == timedelta(minutes=45)
    assert abs(datetime.now() - ultima) < timedelta(minutes=1)


def test_desde_terminal_deja_50_lecturas_por_sensor(tmp_path, monkeypatch):
    # Es el "Está terminada cuando" de la issue, en una carpeta temporal.
    (tmp_path / "data").mkdir()
    shutil.copy(ZONAS_DE_PRUEBA, tmp_path / "data" / "zonas.json")
    monkeypatch.chdir(tmp_path)

    simulador.main(["--rondas", "50", "--semilla", "1"])

    lecturas = RepositorioLecturas(tmp_path / "data" / "lecturas.json")
    for sensor in sensores_de_prueba():
        assert len(lecturas.de_sensor(sensor.id)) == 50