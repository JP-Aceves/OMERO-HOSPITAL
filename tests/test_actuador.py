import pytest

from model.actuador import Actuador, crear_actuador


@pytest.mark.parametrize("encendido", [False, True])
def test_semaforo_antiguo_conserva_su_formato_sin_estado(encendido):
    datos = {
        "id": "A1", "nombre": "Semáforo", "tipo": "led_semaforo",
        "encendido": encendido,
    }

    semaforo = crear_actuador(datos)

    assert semaforo.estado is None
    assert semaforo.to_dict() == datos


@pytest.mark.parametrize("estado", ["normal", "aviso", "critico"])
def test_semaforo_conserva_el_estado_al_reconstruirse(estado):
    semaforo = Actuador("A1", "Semáforo", "led_semaforo")

    semaforo.fijar_estado(estado)

    assert semaforo.estado == estado
    assert semaforo.encendido is False
    semaforo.encender()
    datos = semaforo.to_dict()
    assert datos == {
        "id": "A1", "nombre": "Semáforo", "tipo": "led_semaforo",
        "encendido": True, "estado": estado,
    }
    assert crear_actuador(datos).to_dict() == datos


@pytest.mark.parametrize("estado", ["", "rojo", "verde"])
def test_fijar_estado_rechaza_un_estado_desconocido(estado):
    semaforo = Actuador("A1", "Semáforo", "led_semaforo")

    with pytest.raises(ValueError):
        semaforo.fijar_estado(estado)

    assert semaforo.estado is None
    assert semaforo.encendido is False


@pytest.mark.parametrize("tipo", ["ventilador", "led_evacuacion"])
def test_fijar_estado_no_controla_otros_actuadores(tipo):
    actuador = Actuador("A1", "Otro actuador", tipo, encendido=True)
    datos = actuador.to_dict()

    with pytest.raises(ValueError):
        actuador.fijar_estado("critico")

    assert actuador.to_dict() == datos
