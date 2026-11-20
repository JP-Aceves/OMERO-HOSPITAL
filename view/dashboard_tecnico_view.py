"""Dashboard "Recursos" del técnico de logística (mockup 05). Responsable: Ivan (OME-63)."""
import flet as ft

from controller.tecnico_controller import TecnicoController
from model.usuario import Usuario


class DashboardTecnicoView:

    def __init__(self, usuario: Usuario, controlador: TecnicoController) -> None:
        raise NotImplementedError("OME-63")

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        raise NotImplementedError("OME-63")
