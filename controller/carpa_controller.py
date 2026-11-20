"""Datos del dashboard "Mi carpa" del responsable de carpa. Responsable: Rodas (OME-62).

Se apoya en DashboardController (lecturas, estado y alertas) y en
ActuadoresController (ventilador); la vista no toca el modelo.
"""
from controller.actuadores_controller import ActuadoresController
from controller.dashboard_controller import DashboardController
from model.usuario import Usuario


class CarpaController:

    def __init__(self, dashboard: DashboardController, actuadores: ActuadoresController) -> None:
        raise NotImplementedError("OME-62")

    def resumen(self, usuario: Usuario) -> list[dict]:
        """Las zonas del usuario con el mismo formato que DashboardController.resumen().

        Sensores de la carpa: temperatura, humedad, calidad del aire y luz.
        """
        raise NotImplementedError("OME-62")

    def alertas(self, usuario: Usuario) -> list[dict]:
        """Alertas activas de sus zonas (DashboardController.alertas)."""
        raise NotImplementedError("OME-62")

    def ventilador(self, usuario: Usuario) -> dict | None:
        """{"zona": "Z1", "id": "A1", "nombre": "Ventilador", "encendido": False} o None si no tiene."""
        raise NotImplementedError("OME-62")

    def cambiar_ventilador(self, usuario: Usuario, encendido: bool) -> str | None:
        """None si va bien, o el mensaje de error (usa ActuadoresController.cambiar)."""
        raise NotImplementedError("OME-62")

    def actualizar(self) -> None:
        """Pide una ronda nueva (DashboardController.actualizar)."""
        raise NotImplementedError("OME-62")
