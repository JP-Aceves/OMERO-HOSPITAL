"""Sensores de OMERO: una clase abstracta y una subclase por tipo. Responsable: Medina (OME-31).

Mismo patrón que Usuario: herencia + fábrica crear_sensor(dict).
Cada subclase solo define TIPO, MODELO, UNIDAD, RANGO (lo usa el simulador) e INVERSO.

INVERSO = False: el sensor es malo cuando SUBE (aviso < crítico, p. ej. 28 / 32 °C).
INVERSO = True:  el sensor es malo cuando BAJA (aviso > crítico, p. ej. depósito 50 / 20 %).
Umbrales oficiales: tabla "Umbrales iniciales por sensor" del documento del proyecto (ver README).
Los MQ (calidad del aire y humo/gas) se miden en % sobre el valor base en aire limpio.
"""
from abc import ABC, abstractmethod


class Sensor(ABC):
    @property
    @abstractmethod
    def TIPO(self) -> str:
        """Identificador que debe definir cada tipo de sensor."""

    MODELO: str = ""
    UNIDAD: str = ""
    RANGO: tuple[float, float] = (0, 0)
    INVERSO: bool = False

    def __init__(self, id: str, nombre: str, umbral_aviso: float, umbral_critico: float) -> None:
        self.id = id
        self.nombre = nombre
        self.umbral_aviso = umbral_aviso
        self.umbral_critico = umbral_critico

    def to_dict(self) -> dict:
        """{"id", "nombre", "tipo", "umbral_aviso", "umbral_critico"} para guardar en zonas.json."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.TIPO,
            "umbral_aviso": self.umbral_aviso,
            "umbral_critico": self.umbral_critico,
        }


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
    UNIDAD = "%"           # % sobre la base
    RANGO = (0, 100)


class SensorLuz(Sensor):
    TIPO = "luz"
    MODELO = "LDR"
    UNIDAD = "%"
    RANGO = (0, 100)
    INVERSO = True         # malo si baja (corte de luz)


class SensorHumoGas(Sensor):
    TIPO = "humo_gas"
    MODELO = "MQ-2"
    UNIDAD = "%"           # % sobre la base
    RANGO = (0, 100)


class SensorNivelDeposito(Sensor):
    TIPO = "nivel_deposito"
    MODELO = "HC-SR04"
    UNIDAD = "%"
    RANGO = (0, 100)
    INVERSO = True         # malo si baja (se vacía)


class SensorViento(Sensor):
    TIPO = "viento"
    MODELO = "Anemómetro"
    UNIDAD = "km/h"
    RANGO = (0, 90)


def crear_sensor(datos: dict) -> Sensor:
    """Crea la subclase correcta según datos["tipo"]. ValueError si el tipo no existe."""
    clases = {
        SensorTemperatura.TIPO: SensorTemperatura,
        SensorHumedad.TIPO: SensorHumedad,
        SensorCalidadAire.TIPO: SensorCalidadAire,
        SensorLuz.TIPO: SensorLuz,
        SensorHumoGas.TIPO: SensorHumoGas,
        SensorNivelDeposito.TIPO: SensorNivelDeposito,
        SensorViento.TIPO: SensorViento,
    }
    tipo = datos["tipo"]
    clase = clases.get(tipo) if isinstance(tipo, str) else None
    if clase is None:
        raise ValueError(f"Tipo de sensor desconocido: {tipo}")
    return clase(
        id=datos["id"],
        nombre=datos["nombre"],
        umbral_aviso=datos["umbral_aviso"],
        umbral_critico=datos["umbral_critico"],
    )
