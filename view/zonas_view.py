"""Pantalla "Zonas y sensores" del jefe de sanidad (mockup 06). Responsable: JP (OME-35)."""
import flet as ft

from controller.zonas_controller import ZonasController
from model.usuario import Usuario


class ZonasView:

    def __init__(self, usuario: Usuario, controlador: ZonasController) -> None:
        raise NotImplementedError("OME-35")

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        raise NotImplementedError("OME-35")
