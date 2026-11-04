"""Simulador de lecturas hasta que llegue el ESP32. Responsable: Ivan (OME-33).

Uso desde terminal:  python -m service.simulador --rondas 50
"""
from model.lista_enlazada import ListaEnlazada
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas


class Simulador:

    def __init__(self, repo_zonas: RepositorioZonas, repo_lecturas: RepositorioLecturas, semilla: int | None = None) -> None:
        raise NotImplementedError("OME-33")

    def generar_ronda(self) -> ListaEnlazada:
        """Una Lectura por cada sensor de cada zona. La guarda y la devuelve."""
        raise NotImplementedError("OME-33")

    def generar(self, rondas: int, minutos_entre: int = 5) -> None:
        """Genera varias rondas seguidas con fechas separadas (histórico de golpe)."""
        raise NotImplementedError("OME-33")


def main() -> None:
    raise NotImplementedError("OME-33")


if __name__ == "__main__":
    main()
