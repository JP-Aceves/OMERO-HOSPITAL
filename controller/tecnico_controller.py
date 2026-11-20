"""Datos del dashboard "Recursos" del técnico de logística. Responsable: Ivan (OME-63).

Se apoya en DashboardController (lecturas, estado y alertas), en
service/prediccion.py (vaciado del depósito) y en ActuadoresController (LED).
"""
from controller.actuadores_controller import ActuadoresController
from controller.dashboard_controller import DashboardController
from model.usuario import Usuario
from persistence.repositorio_lecturas import RepositorioLecturas


class TecnicoController:

    def __init__(self, dashboard: DashboardController, actuadores: ActuadoresController,
                 repo_lecturas: RepositorioLecturas) -> None:
        raise NotImplementedError("OME-63")

    def resumen(self, usuario: Usuario) -> list[dict]:
        """Las zonas del usuario con el mismo formato que DashboardController.resumen().

        Sensores: depósito, humo/gas y viento.
        """
        raise NotImplementedError("OME-63")

    def deposito(self, usuario: Usuario) -> dict | None:
        """{"zona": "Z2", "nivel": 43.0, "estado": "aviso", "vaciado": "2026-11-27T10:00:00" | None,
        "historico": [(fecha_hora, nivel), ...]} o None si no tiene depósito."""
        raise NotImplementedError("OME-63")

    def alertas(self, usuario: Usuario) -> list[dict]:
        """Alertas activas de sus zonas (DashboardController.alertas)."""
        raise NotImplementedError("OME-63")

    def led_evacuacion(self, usuario: Usuario) -> dict | None:
        """{"zona": "Z2", "id": "A3", "nombre": "Tira LED de evacuación", "encendido": False} o None."""
        raise NotImplementedError("OME-63")

    def cambiar_led(self, usuario: Usuario, encendido: bool) -> str | None:
        """None si va bien, o el mensaje de error (usa ActuadoresController.cambiar)."""
        raise NotImplementedError("OME-63")

    def actualizar(self) -> None:
        """Pide una ronda nueva (DashboardController.actualizar)."""
        raise NotImplementedError("OME-63")
