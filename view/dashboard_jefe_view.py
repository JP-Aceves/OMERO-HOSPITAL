"""Dashboard "Estado global" del jefe de sanidad (mockup 03). Responsable: Medina (OME-40)."""
import flet as ft

from controller.dashboard_controller import DashboardController
from model.usuario import Usuario


class DashboardJefeView:

    def __init__(self, usuario: Usuario, controlador: DashboardController) -> None:
        raise NotImplementedError("OME-40")

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        raise NotImplementedError("OME-40")
