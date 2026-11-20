"""Pantalla "Cuenta pendiente" para quien se acaba de registrar. Responsable: Mariana (OME-61).

Explica que el administrador tiene que asignarle un rol y deja cerrar sesión.
"""
import flet as ft

from model.usuario import Usuario


class PendienteView:

    def __init__(self, usuario: Usuario) -> None:
        raise NotImplementedError("OME-61")

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        raise NotImplementedError("OME-61")
