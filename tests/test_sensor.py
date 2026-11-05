import pytest

from model.sensor import (
    Sensor,
    SensorCalidadAire,
    SensorHumedad,
    SensorHumoGas,
    SensorLuz,
    SensorNivelDeposito,
    SensorTemperatura,
    SensorViento,
    crear_sensor,
)


@pytest.mark.parametrize(
    ("tipo", "clase", "modelo", "unidad", "rango", "aviso", "critico", "inverso"),
    [
        pytest.param(
            "temperatura", SensorTemperatura, "DHT22", "°C", (15, 45), 28, 32, False,
            id="temperatura",
        ),
        pytest.param(
            "humedad", SensorHumedad, "DHT22", "%", (20, 95), 60, 70, False,
            id="humedad",
        ),
        pytest.param(
            "calidad_aire", SensorCalidadAire, "MQ-135", "%", (0, 100), 20, 50, False,
            id="calidad-aire",
        ),
        pytest.param(
            "luz", SensorLuz, "LDR", "%", (0, 100), 40, 20, True,
            id="luz",
        ),
        pytest.param(
            "humo_gas", SensorHumoGas, "MQ-2", "%", (0, 100), 20, 50, False,
            id="humo-gas",
        ),
        pytest.param(
            "nivel_deposito", SensorNivelDeposito, "HC-SR04", "%", (0, 100), 50, 20, True,
            id="nivel-deposito",
        ),
        pytest.param(
            "viento", SensorViento, "Anemómetro", "km/h", (0, 90), 30, 50, False,
            id="viento",
        ),
    ],
)
def test_fabrica_reconstruye_el_tipo_y_el_diccionario_a03(
    tipo, clase, modelo, unidad, rango, aviso, critico, inverso
):
    datos = {
        "id": "S1",
        "nombre": "Sensor de prueba",
        "tipo": tipo,
        "umbral_aviso": aviso,
        "umbral_critico": critico,
    }

    sensor = crear_sensor(datos)

    assert type(sensor) is clase
    assert (sensor.id, sensor.nombre) == ("S1", "Sensor de prueba")
    assert (sensor.umbral_aviso, sensor.umbral_critico) == (aviso, critico)
    assert (sensor.TIPO, sensor.MODELO, sensor.UNIDAD, sensor.RANGO) == (
        tipo, modelo, unidad, rango
    )
    assert sensor.INVERSO is inverso
    assert sensor.to_dict() == datos


def test_fabrica_rechaza_un_tipo_desconocido():
    with pytest.raises(ValueError):
        crear_sensor({
            "id": "S1",
            "nombre": "Sensor no compatible",
            "tipo": "presion",
            "umbral_aviso": 28,
            "umbral_critico": 32,
        })


def test_sensor_base_es_abstracto():
    with pytest.raises(TypeError):
        Sensor("S1", "Sensor sin tipo", 28, 32)
