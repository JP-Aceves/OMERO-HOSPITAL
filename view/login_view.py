"""Pantalla de login. Responsable: Rodas (OME-23)."""
from typing import Callable

import flet as ft


class LoginView:
    RUTA = "/login"

    def __init__(self, al_entrar: Callable[[str, str], str | None], al_ir_registro: Callable[[], None]) -> None:
        """al_entrar(usuario, contrasena) devuelve None si entra, o el mensaje de error."""
        self.al_entrar = al_entrar
        self.al_ir_registro = al_ir_registro

    def construir(self) -> ft.View:
        # Provisional: Rodas lo sustituye por el diseño del mockup.
        return ft.View(self.RUTA, [ft.Text("Login pendiente (OME-23)")])
