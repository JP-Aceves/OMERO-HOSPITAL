import pytest

from model.alerta import Alerta
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import (
    SensorCalidadAire,
    SensorHumedad,
    SensorHumoGas,
    SensorLuz,
    SensorNivelDeposito,
    SensorTemperatura,
    SensorViento,
)
from model.zona import Zona
from service.alertas import alertas_de_ronda, alertas_de_zonas, hay_alerta_critica


def lista_de(*elementos):
    resultado = ListaEnlazada()
    for elemento in elementos:
        resultado.insertar(elemento)
    return resultado


@pytest.mark.parametrize(
    ("clase", "aviso", "critico"),
    [
        (SensorTemperatura, 28, 32),
        (SensorHumedad, 60, 70),
        (SensorCalidadAire, 20, 50),
        (SensorLuz, 40, 20),
        (SensorHumoGas, 20, 50),
        (SensorNivelDeposito, 50, 20),
        (SensorViento, 30, 50),
    ],
    ids=("temperatura", "humedad", "aire", "luz", "humo", "deposito", "viento"),
)
def test_umbrales_inclusivos_y_normal_en_los_siete_sensores(clase, aviso, critico):
    sensor = clase("S1", "Sensor de prueba", aviso, critico)
    zona = Zona("Z1", "Carpa", "carpa")
    zona.anadir_sensor(sensor)
    sentido = 1 if sensor.INVERSO else -1

    for valor, nivel in (
        (aviso + sentido * 0.1, None),
        (aviso, "aviso"),
        (critico + sentido * 0.1, "aviso"),
        (critico, "critico"),
    ):
        lectura = Lectura("Z1", "S1", sensor.TIPO, valor, sensor.UNIDAD, "2026-11-20T18:00:00")

        alertas = alertas_de_ronda(lista_de(zona), lista_de(lectura))

        assert isinstance(alertas, ListaEnlazada)
        if nivel is None:
            assert len(alertas) == 0
        else:
            assert len(alertas) == 1
            alerta = next(iter(alertas))
            assert isinstance(alerta, Alerta)
            assert alerta.to_dict() == {
                "zona": "Z1", "sensor": "S1", "tipo": sensor.TIPO,
                "valor": valor, "unidad": sensor.UNIDAD, "nivel": nivel,
                "fecha_hora": "2026-11-20T18:00:00",
            }


@pytest.mark.parametrize("nivel", ["normal", "urgente", ""])
def test_modelo_alerta_rechaza_niveles_desconocidos(nivel):
    with pytest.raises(ValueError):
        Alerta("Z1", "S1", "temperatura", 33, "°C", nivel, "2026-11-20T18:00:00")


@pytest.mark.parametrize(("valor", "nivel"), [(29, "aviso"), (25, None)])
def test_duplicados_del_sensor_solo_cuentan_la_ultima_lectura(valor, nivel):
    zona = Zona("Z1", "Carpa", "carpa")
    zona.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    lecturas = lista_de(
        Lectura("Z1", "S1", "temperatura", 34, "°C", "2026-11-20T18:00:00"),
        Lectura("Z1", "S1", "temperatura", valor, "°C", "2026-11-20T18:01:00"),
    )

    alertas = alertas_de_ronda(lista_de(zona), lecturas)

    assert len(alertas) == (0 if nivel is None else 1)
    if nivel is not None:
        alerta = next(iter(alertas))
        assert (alerta.valor, alerta.nivel, alerta.fecha_hora) == (
            valor, nivel, "2026-11-20T18:01:00"
        )


def test_descarta_zona_sensor_o_tipo_que_no_corresponden():
    zona = Zona("Z1", "Carpa", "carpa")
    zona.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    lecturas = lista_de(
        Lectura("Z9", "S1", "temperatura", 35, "°C", "2026-11-20T18:00:00"),
        Lectura("Z1", "S9", "temperatura", 35, "°C", "2026-11-20T18:00:00"),
        Lectura("Z1", "S1", "humedad", 95, "%", "2026-11-20T18:00:00"),
    )

    assert len(alertas_de_ronda(lista_de(zona), lecturas)) == 0
    assert len(alertas_de_ronda(ListaEnlazada(), lecturas)) == 0
    assert len(alertas_de_ronda(lista_de(zona), ListaEnlazada())) == 0


def test_una_lectura_incoherente_no_reemplaza_una_alerta_valida():
    zona = Zona("Z1", "Carpa", "carpa")
    zona.anadir_sensor(SensorTemperatura("S1", "Temperatura", 28, 32))
    lecturas = lista_de(
        Lectura("Z1", "S1", "temperatura", 33, "°C", "2026-11-20T18:00:00"),
        Lectura("Z1", "S1", "humedad", 25, "%", "2026-11-20T18:01:00"),
    )

    alertas = alertas_de_ronda(lista_de(zona), lecturas)

    assert len(alertas) == 1
    assert next(iter(alertas)).tipo == "temperatura"


def test_filtro_por_zonas_conserva_solo_las_asignadas_sin_modificar_origen():
    alertas = lista_de(
        Alerta("Z1", "S1", "temperatura", 33, "°C", "critico", "2026-11-20T18:00:00"),
        Alerta("Z2", "S2", "humo_gas", 22, "%", "aviso", "2026-11-20T18:00:00"),
        Alerta("Z3", "S3", "viento", 50, "km/h", "critico", "2026-11-20T18:00:00"),
    )

    filtradas = alertas_de_zonas(alertas, lista_de("Z1", "Z3"))

    assert isinstance(filtradas, ListaEnlazada)
    assert [(alerta.zona, alerta.sensor) for alerta in filtradas] == [("Z1", "S1"), ("Z3", "S3")]
    assert len(alertas) == 3
    assert len(alertas_de_zonas(alertas, ListaEnlazada())) == 0


def test_hay_alerta_critica_usa_humo_gas_por_defecto_y_admite_otro_tipo():
    alertas = lista_de(
        Alerta("Z1", "S1", "temperatura", 33, "°C", "critico", "2026-11-20T18:00:00"),
        Alerta("Z2", "S2", "humo_gas", 22, "%", "aviso", "2026-11-20T18:00:00"),
    )

    assert hay_alerta_critica(alertas) is False
    assert hay_alerta_critica(alertas, "temperatura") is True
    alertas.insertar(
        Alerta("Z2", "S2", "humo_gas", 50, "%", "critico", "2026-11-20T18:01:00")
    )
    assert hay_alerta_critica(alertas) is True
    assert hay_alerta_critica(ListaEnlazada()) is False
