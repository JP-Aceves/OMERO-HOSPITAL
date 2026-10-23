"""Pantalla de registro. Responsable: Medina (OME-24)."""
from typing import Callable

import flet as ft


class RegistroView:
    RUTA = "/registro"

    def __init__(self, al_registrar: Callable[[str, str, str, str, str], str | None], al_volver: Callable[[], None]) -> None:
        """al_registrar(nombre, usuario, contrasena, repetir, rol) devuelve None si va bien, o el error."""
        self.al_registrar = al_registrar
        self.al_volver = al_volver

    def construir(self) -> ft.View:
        # Provisional: Medina lo sustituye por el diseño del mockup.
        return ft.View(self.RUTA, [ft.Text("Registro pendiente (OME-24)")])
