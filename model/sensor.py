"""Sensores de OMERO: una clase abstracta y una subclase por tipo. Responsable: Medina (OME-31).

Mismo patrón que Usuario: herencia + fábrica crear_sensor(dict).
Cada subclase solo define TIPO, MODELO, UNIDAD y RANGO (lo usa el simulador).
"""
from abc import ABC


class Sensor(ABC):
    TIPO: str = ""
    MODELO: str = ""
    UNIDAD: str = ""
    RANGO: tuple[float, float] = (0, 0)

    def __init__(self, id: str, nombre: str, umbral_aviso: float, umbral_critico: float) -> None:
        raise NotImplementedError("OME-31")

    def to_dict(self) -> dict:
        """{"id", "nombre", "tipo", "umbral_aviso", "umbral_critico"} para guardar en zonas.json."""
        raise NotImplementedError("OME-31")


class SensorTemperatura(Sensor):
    TIPO = "temperatura"
    MODELO = "DHT22"
    UNIDAD = "°C"
    RANGO = (15, 45)


class SensorHumedad(Sensor):
    TIPO = "humedad"
    MODELO = "DHT22"
    UNIDAD = "%"
    RANGO = (20, 95)


class SensorCalidadAire(Sensor):
    TIPO = "calidad_aire"
    MODELO = "MQ-135"
    UNIDAD = "ppm"
    RANGO = (300, 2000)


class SensorLuz(Sensor):
    TIPO = "luz"
    MODELO = "LDR"
    UNIDAD = "lux"
    RANGO = (0, 1000)


class SensorHumoGas(Sensor):
    TIPO = "humo_gas"
    MODELO = "MQ-2"
    UNIDAD = "ppm"
    RANGO = (100, 800)


class SensorNivelDeposito(Sensor):
    TIPO = "nivel_deposito"
    MODELO = "HC-SR04"
    UNIDAD = "%"
    RANGO = (0, 100)


class SensorViento(Sensor):
    TIPO = "viento"
    MODELO = "Anemómetro"
    UNIDAD = "km/h"
    RANGO = (0, 90)


def crear_sensor(datos: dict) -> Sensor:
    """Crea la subclase correcta según datos["tipo"]. ValueError si el tipo no existe."""
    raise NotImplementedError("OME-31")
