"""Datos del dashboard del jefe de sanidad. Responsable: Medina (OME-40)."""
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador


class DashboardController:

    def __init__(self, repo_zonas: RepositorioZonas, repo_lecturas: RepositorioLecturas, simulador: Simulador) -> None:
        raise NotImplementedError("OME-40")

    def resumen(self) -> list[dict]:
        """Una entrada por zona, lista para pintar (la vista no toca el modelo):

        {"id": "Z1", "nombre": "...", "responsable": "carpa", "estado": "aviso",
         "sensores": [{"nombre": "...", "valor": 31.4, "unidad": "°C", "estado": "aviso"}, ...]}
        Si un sensor aún no tiene lecturas: "valor": None y "estado": "normal".
        La list solo se crea aquí para entregar los datos a la vista; los datos viven en ListaEnlazada.
        """
        raise NotImplementedError("OME-40")

    def contadores(self) -> dict:
        """{"normal": 1, "aviso": 1, "critico": 1} contando zonas."""
        raise NotImplementedError("OME-40")

    def actualizar(self) -> None:
        """Pide una ronda nueva al simulador."""
        raise NotImplementedError("OME-40")
