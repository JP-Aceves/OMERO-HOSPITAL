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
        campo_usuario = ft.TextField(
            label="Usuario",
            hint_text="Introduce tu usuario",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            autofocus=True,
        )
        campo_contrasena = ft.TextField(
            label="Contraseña",
            hint_text="Introduce tu contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
        )
        mensaje_error = ft.Text(color="#B42318", size=13)

        def entrar(_evento=None) -> None:
            error = self.al_entrar(
                campo_usuario.value or "",
                campo_contrasena.value or "",
            )
            if error is not None:
                mensaje_error.value = error
                mensaje_error.update()

        contenido = ft.Column(
            controls=[
                ft.Text("OMERO", size=34, weight=ft.FontWeight.BOLD, color="#174A7E"),
                ft.Text(
                    "Monitor de hospital de campaña",
                    size=15,
                    color="#526171",
                ),
                ft.Divider(height=20, color="transparent"),
                campo_usuario,
                campo_contrasena,
                ft.ElevatedButton(
                    text="Entrar",
                    icon=ft.Icons.LOGIN,
                    on_click=entrar,
                    width=356,
                ),
                mensaje_error,
                ft.Row(
                    controls=[
                        ft.Text("¿Todavía no tienes cuenta?", size=13),
                        ft.TextButton(
                            text="Regístrate",
                            on_click=lambda _evento: self.al_ir_registro(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        )
        tarjeta = ft.Container(
            content=contenido,
            width=420,
            padding=32,
            bgcolor="#FFFFFF",
            border_radius=16,
        )
        return ft.View(
            self.RUTA,
            [ft.Container(content=tarjeta, expand=True, alignment=ft.alignment.center)],
            bgcolor="#F3F6FA",
        )
