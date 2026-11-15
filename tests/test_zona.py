import json

import pytest

from model.actuador import Actuador, crear_actuador
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorNivelDeposito, SensorTemperatura
from model.zona import Zona, crear_zona


@pytest.fixture
def datos_zona():
    return {
        "id": "Z1",
        "nombre": "Carpa de hospitalización",
        "tipo": "carpa",
        "responsable": "carpa",
        "sensores": [
            {
                "id": "S1",
                "nombre": "Temperatura",
                "tipo": "temperatura",
                "umbral_aviso": 28,
                "umbral_critico": 32,
            },
            {
                "id": "S2",
                "nombre": "Depósito",
                "tipo": "nivel_deposito",
                "umbral_aviso": 50,
                "umbral_critico": 20,
            },
        ],
        "actuadores": [
            {"id": "A1", "nombre": "Ventilador", "tipo": "ventilador", "encendido": False},
            {"id": "A2", "nombre": "Semáforo", "tipo": "led_semaforo", "encendido": True},
        ],
    }


def test_zona_se_reconstruye_desde_json_con_sus_dispositivos(datos_zona):
    zona = crear_zona(datos_zona)
    reconstruida = crear_zona(json.loads(json.dumps(zona.to_dict())))

    assert reconstruida.to_dict() == datos_zona
    assert isinstance(reconstruida.sensores, ListaEnlazada)
    assert isinstance(reconstruida.actuadores, ListaEnlazada)
    assert isinstance(reconstruida.buscar_sensor("S1"), SensorTemperatura)
    assert isinstance(reconstruida.buscar_sensor("S2"), SensorNivelDeposito)
    assert all(isinstance(actuador, Actuador) for actuador in reconstruida.actuadores)


@pytest.mark.parametrize("tipo", ["carpa", "zona_tecnica", "exterior"])
def test_zona_nueva_no_tiene_responsable_ni_dispositivos(tipo):
    zona = Zona("Z1", "Zona de prueba", tipo)

    assert zona.to_dict() == {
        "id": "Z1",
        "nombre": "Zona de prueba",
        "tipo": tipo,
        "responsable": None,
        "sensores": [],
        "actuadores": [],
    }
    assert isinstance(zona.sensores, ListaEnlazada)
    assert isinstance(zona.actuadores, ListaEnlazada)


def test_zona_rechaza_un_tipo_desconocido():
    with pytest.raises(ValueError):
        Zona("Z1", "Almacén", "almacen")


def test_zona_anade_busca_y_elimina_sensores():
    zona = Zona("Z1", "Carpa", "carpa")
    sensor = SensorTemperatura("S1", "Temperatura", 28, 32)

    assert zona.buscar_sensor("S1") is None
    zona.anadir_sensor(sensor)
    assert zona.buscar_sensor("S1") is sensor
    assert zona.eliminar_sensor("S1") is True
    assert zona.buscar_sensor("S1") is None
    assert zona.eliminar_sensor("S1") is False


def test_zona_anade_y_elimina_actuadores():
    zona = Zona("Z1", "Carpa", "carpa")
    actuador = Actuador("A1", "Ventilador", "ventilador")

    zona.anadir_actuador(actuador)
    assert next(iter(zona.actuadores)) is actuador
    assert zona.eliminar_actuador("A1") is True
    assert len(zona.actuadores) == 0
    assert zona.eliminar_actuador("A1") is False


@pytest.mark.parametrize("coleccion", ["sensores", "actuadores"])
def test_crear_zona_rechaza_ids_repetidos(datos_zona, coleccion):
    datos_zona[coleccion].append({**datos_zona[coleccion][0], "nombre": "Repetido"})

    with pytest.raises(ValueError):
        crear_zona(datos_zona)


@pytest.mark.parametrize("tipo", ["ventilador", "led_semaforo", "led_evacuacion"])
def test_actuador_conserva_el_estado_al_reconstruirse(tipo):
    actuador = Actuador("A1", "Actuador de prueba", tipo)

    assert actuador.encendido is False
    actuador.encender()
    reconstruido = crear_actuador(actuador.to_dict())
    assert reconstruido.to_dict() == {
        "id": "A1", "nombre": "Actuador de prueba", "tipo": tipo, "encendido": True
    }
    reconstruido.apagar()
    assert reconstruido.encendido is False


def test_crear_actuador_rechaza_un_tipo_desconocido():
    with pytest.raises(ValueError):
        crear_actuador({"id": "A1", "nombre": "Bomba", "tipo": "bomba", "encendido": False})


def test_lectura_respeta_el_formato_del_esp32():
    datos = {
        "zona": "Z1",
        "sensor": "S1",
        "tipo": "temperatura",
        "valor": 31.4,
        "unidad": "°C",
        "fecha_hora": "2026-11-10T18:30:00",
    }

    lectura = Lectura.desde_dict(datos)

    assert isinstance(lectura, Lectura)
    assert lectura.to_dict() == datos
