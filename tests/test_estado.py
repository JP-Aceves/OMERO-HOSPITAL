import pytest

from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorLuz, SensorNivelDeposito, SensorTemperatura
from service.estado import estado_sensor, peor_estado


@pytest.mark.parametrize(
    ("clase", "aviso", "critico", "casos"),
    [
        pytest.param(
            SensorTemperatura, 28, 32,
            ((27.9, "normal"), (28, "aviso"), (31.9, "aviso"), (32, "critico")),
            id="temperatura",
        ),
        pytest.param(
            SensorLuz, 40, 20,
            ((40.1, "normal"), (40, "aviso"), (20.1, "aviso"), (20, "critico")),
            id="luz",
        ),
        pytest.param(
            SensorNivelDeposito, 50, 20,
            ((50.1, "normal"), (50, "aviso"), (20.1, "aviso"), (20, "critico")),
            id="deposito",
        ),
    ],
)
def test_estado_sensor_incluye_los_dos_umbrales(clase, aviso, critico, casos):
    sensor = clase("S1", "Sensor de prueba", aviso, critico)

    for valor, esperado in casos:
        assert estado_sensor(sensor, valor) == esperado, f"Valor: {valor}"


@pytest.mark.parametrize(
    ("estados", "esperado"),
    [
        ((), "normal"),
        (("normal", "normal"), "normal"),
        (("normal", "aviso", "normal"), "aviso"),
        (("normal", "critico", "aviso"), "critico"),
    ],
    ids=("vacia", "normal", "aviso", "critico"),
)
def test_peor_estado_devuelve_el_mas_grave(estados, esperado):
    lista = ListaEnlazada()
    for estado in estados:
        lista.insertar(estado)

    assert peor_estado(lista) == esperado
