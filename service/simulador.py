"""Simulador de lecturas hasta que llegue el ESP32. Responsable: Ivan (OME-33).

Uso desde terminal:  python -m service.simulador --rondas 50
"""
import argparse
import random
from datetime import datetime, timedelta

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import Sensor, SensorNivelDeposito
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas

VUELTA_A_LO_NORMAL = 0.2      # en cada ronda recorre un 20 % del camino hacia su valor normal
RUIDO = 0.03                  # variación aleatoria: un 3 % del rango del sensor
PROBABILIDAD_PICO = 0.05      # 1 de cada 20 lecturas se dispara más allá del umbral crítico
CONSUMO_DEPOSITO = (0.5, 2.0)  # puntos que baja el depósito en cada ronda
NIVEL_RELLENO = 10            # si el depósito baja de aquí, se rellena


class Simulador:

    def __init__(self, repo_zonas: RepositorioZonas, repo_lecturas: RepositorioLecturas, semilla: int | None = None) -> None:
        self.repo_zonas = repo_zonas
        self.repo_lecturas = repo_lecturas
        self._azar = random.Random(semilla)

    def generar_ronda(self) -> ListaEnlazada:
        """Una Lectura por cada sensor de cada zona. La guarda y la devuelve."""
        return self._ronda(datetime.now())

    def generar(self, rondas: int, minutos_entre: int = 5) -> None:
        """Genera varias rondas seguidas con fechas separadas (histórico de golpe)."""
        inicio = datetime.now() - timedelta(minutes=minutos_entre * (rondas - 1))
        for numero in range(rondas):
            self._ronda(inicio + timedelta(minutes=minutos_entre * numero))

    def _ronda(self, momento: datetime) -> ListaEnlazada:
        fecha_hora = momento.isoformat(timespec="seconds")
        lecturas = ListaEnlazada()
        for zona in self.repo_zonas.listar():
            for sensor in zona.sensores:
                valor = round(self._siguiente_valor(sensor), 1)
                lecturas.insertar(Lectura(zona.id, sensor.id, sensor.TIPO, valor, sensor.UNIDAD, fecha_hora))
        self.repo_lecturas.anadir(lecturas)
        return lecturas

    def _siguiente_valor(self, sensor: Sensor) -> float:
        anterior = self.repo_lecturas.ultima(sensor.id)
        if isinstance(sensor, SensorNivelDeposito):
            return self._nivel_deposito(anterior)
        if self._azar.random() < PROBABILIDAD_PICO:
            return self._pico(sensor)
        normal = _valor_normal(sensor)
        if anterior is None or _es_critico(sensor, anterior.valor):
            actual = normal
        else:
            actual = anterior.valor
        minimo, maximo = sensor.RANGO
        nuevo = actual + VUELTA_A_LO_NORMAL * (normal - actual) + self._azar.gauss(0, RUIDO * (maximo - minimo))
        return min(max(nuevo, minimo), maximo)

    def _pico(self, sensor: Sensor) -> float:
        minimo, maximo = sensor.RANGO
        if sensor.INVERSO:
            return self._azar.uniform(minimo, sensor.umbral_critico)
        return self._azar.uniform(sensor.umbral_critico, maximo)

    def _nivel_deposito(self, anterior: Lectura | None) -> float:
        if anterior is None:
            return self._azar.uniform(90, 100)
        nivel = anterior.valor - self._azar.uniform(*CONSUMO_DEPOSITO)
        if nivel <= NIVEL_RELLENO:
            return self._azar.uniform(90, 100)
        return nivel


def _valor_normal(sensor: Sensor) -> float:
    """El centro de la zona verde: entre el mínimo y el aviso, o entre el aviso y el máximo si es INVERSO."""
    minimo, maximo = sensor.RANGO
    if sensor.INVERSO:
        return (sensor.umbral_aviso + maximo) / 2
    return (minimo + sensor.umbral_aviso) / 2


def _es_critico(sensor: Sensor, valor: float) -> bool:
    if sensor.INVERSO:
        return valor <= sensor.umbral_critico
    return valor >= sensor.umbral_critico


def main(argumentos: list[str] | None = None) -> None:
    lector = argparse.ArgumentParser(description="Genera lecturas simuladas en data/lecturas.json.")
    lector.add_argument("--rondas", type=int, default=50, help="rondas a generar (una lectura por sensor)")
    lector.add_argument("--minutos", type=int, default=5, help="minutos entre una ronda y la siguiente")
    lector.add_argument("--semilla", type=int, default=None, help="para repetir exactamente los mismos valores")
    opciones = lector.parse_args(argumentos)
    repo_lecturas = RepositorioLecturas()
    Simulador(RepositorioZonas(), repo_lecturas, opciones.semilla).generar(opciones.rondas, opciones.minutos)
    print(f"{opciones.rondas} rondas generadas en {repo_lecturas.ruta}")


if __name__ == "__main__":
    main()