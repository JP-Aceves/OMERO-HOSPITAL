"""Pantalla de inicio según el rol. Responsable: JP (OME-25)."""
import flet as ft

from controller.zonas_controller import ZonasController
from model.usuario import Usuario


class InicioView:

    def __init__(self, usuario: Usuario, zonas: ZonasController) -> None:
        raise NotImplementedError("OME-25")

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        raise NotImplementedError("OME-25")
