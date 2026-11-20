"""Dashboard "Mi carpa" del responsable de carpa (mockup 04). Responsable: Rodas (OME-62)."""
import flet as ft

from controller.carpa_controller import CarpaController
from model.usuario import Usuario


class DashboardCarpaView:

    def __init__(self, usuario: Usuario, controlador: CarpaController) -> None:
        raise NotImplementedError("OME-62")

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        raise NotImplementedError("OME-62")
