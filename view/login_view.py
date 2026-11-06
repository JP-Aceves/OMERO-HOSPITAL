"""Pantalla de login. Responsable: Rodas (OME-36)."""
from typing import Callable

import flet as ft

from view import tema


class LoginView:
    RUTA = "/login"

    def __init__(self, al_entrar: Callable[[str, str], str | None], al_ir_registro: Callable[[], None]) -> None:
        self.al_entrar = al_entrar
        self.al_ir_registro = al_ir_registro

    def construir(self) -> ft.View:
        campo_contrasena = tema.campo_texto(
            "Contraseña", hint_text="Introduce tu contraseña", prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True, key="test:login_contrasena")
        mensaje_error = ft.Text("", key="test:login_error", color=tema.CRITICO, size=13)

        def entrar(_evento=None) -> None:
            error = self.al_entrar(campo_usuario.value or "", campo_contrasena.value or "")
            if error is not None:
                mensaje_error.value = error
                mensaje_error.update()

        def pasar_a_contrasena(_evento=None) -> None:
            campo_contrasena.focus()

        campo_usuario = tema.campo_texto(
            "Usuario", hint_text="Introduce tu usuario", prefix_icon=ft.Icons.PERSON_OUTLINE,
            autofocus=True, key="test:login_usuario", on_submit=pasar_a_contrasena)
        campo_contrasena.on_submit = entrar
        contenido = ft.Column(
            controls=[
                ft.Text("OMERO", size=36, weight=ft.FontWeight.BOLD,
                    color=tema.PANEL, font_family=tema.FUENTE_TITULOS),
                ft.Text("Monitor de hospital de campaña", size=15, color=tema.TEXTO_SUAVE),
                ft.Divider(height=20, color="transparent"),
                campo_usuario,
                campo_contrasena,
                tema.boton_primario("Entrar", entrar, icono=ft.Icons.LOGIN, key="test:login_enviar"),
                mensaje_error,
                ft.Row(controls=[
                    ft.Text("¿Todavía no tienes cuenta?", size=13),
                    ft.TextButton("Regístrate", on_click=lambda _evento: self.al_ir_registro()),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=12,
            tight=True,
        )
        tarjeta = ft.Container(
            content=contenido, padding=32, bgcolor=tema.TARJETA, border_radius=16,
            border=ft.border.all(1, tema.BORDE),
        )
        responsive = ft.ResponsiveRow(
            [ft.Container(content=tarjeta, col={"xs": 12, "sm": 10, "md": 8, "lg": 6, "xl": 4})],
            alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True, spacing=0, run_spacing=0,
        )
        return ft.View(self.RUTA, [ft.Container(content=responsive, expand=True, padding=24)],
            bgcolor=tema.FONDO, scroll=ft.ScrollMode.AUTO)
