"""Gestión de usuarios del administrador. Responsable: Medina (OME-57)."""
import flet as ft

from controller.usuarios_controller import UsuariosController
from model.usuario import Usuario


class UsuariosView:

    def __init__(self, usuario: Usuario, controlador: UsuariosController) -> None:
        raise NotImplementedError("OME-57")

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        raise NotImplementedError("OME-57")
