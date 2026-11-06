"""Pantalla de registro. Responsable: Medina (OME-24)."""
from typing import Callable

import flet as ft

from view import tema


class RegistroView:
    RUTA = "/registro"

    def __init__(self, al_registrar: Callable[[str, str, str, str, str], str | None], al_volver: Callable[[], None]) -> None:
        """al_registrar(nombre, usuario, contrasena, repetir, rol) devuelve None si va bien, o el error."""
        self.al_registrar = al_registrar
        self.al_volver = al_volver

    def construir(self) -> ft.View:
        estilo_campo = {
            "border_radius": 8,
            "border_color": tema.BORDE,
            "focused_border_color": tema.PRIMARIO,
            "color": tema.TEXTO,
            "label_style": ft.TextStyle(color=tema.TEXTO_SUAVE),
            "text_size": 14,
            "filled": True,
            "fill_color": tema.TARJETA,
        }
        nombre = ft.TextField(
            key="test:registro_nombre", label="Nombre", autofocus=True, **estilo_campo
        )
        usuario = ft.TextField(
            key="test:registro_usuario", label="Usuario", autocorrect=False,
            enable_suggestions=False, **estilo_campo,
        )
        contrasena = ft.TextField(
            key="test:registro_contrasena", label="Contraseña", password=True,
            can_reveal_password=True, autocorrect=False, enable_suggestions=False,
            col={"xs": 12, "sm": 6}, **estilo_campo,
        )
        repetir = ft.TextField(
            key="test:registro_repetir", label="Repetir contraseña", password=True,
            can_reveal_password=True, autocorrect=False, enable_suggestions=False,
            col={"xs": 12, "sm": 6}, **estilo_campo,
        )
        rol = ft.Dropdown(
            key="test:registro_rol", label="Rol", hint_text="Selecciona tu rol", expand=True,
            options=[
                ft.dropdown.Option("jefe_sanidad", "Jefe de sanidad"),
                ft.dropdown.Option("responsable_carpa", "Responsable de carpa"),
                ft.dropdown.Option("tecnico_logistica", "Técnico de logística"),
            ],
            **estilo_campo,
        )
        mensaje_error = ft.Text(
            "", key="test:registro_error", color=tema.CRITICO, size=13, visible=False
        )

        def registrar(_):
            error = self.al_registrar(
                nombre.value or "", usuario.value or "", contrasena.value or "",
                repetir.value or "", rol.value or "",
            )
            if error is not None:
                mensaje_error.value = error
                mensaje_error.visible = True
                mensaje_error.update()

        repetir.on_submit = registrar
        botones = ft.ResponsiveRow(
            [
                ft.OutlinedButton(
                    "Volver al login", key="test:registro_volver",
                    on_click=lambda _: self.al_volver(), height=44,
                    col={"xs": 12, "sm": 6},
                    style=ft.ButtonStyle(
                    color=tema.PRIMARIO, side=ft.BorderSide(1, tema.PRIMARIO),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
                ft.ElevatedButton(
                    "Registrarme", key="test:registro_enviar", on_click=registrar,
                    height=44, col={"xs": 12, "sm": 6},
                    style=ft.ButtonStyle(
                        color=tema.TARJETA, bgcolor=tema.PRIMARIO, elevation=0,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
            spacing=12, run_spacing=12,
        )
        tarjeta = ft.Container(
            padding=28, bgcolor=tema.TARJETA,
            border=ft.border.all(1, "#DFE6EE"), border_radius=16,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.DONUT_LARGE, color=tema.PRIMARIO, size=26),
                            ft.Text(
                                "OMERO", size=18, weight=ft.FontWeight.BOLD,
                                font_family=tema.FUENTE_TITULOS,
                                color=tema.TEXTO,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "Crear cuenta", size=26, weight=ft.FontWeight.BOLD,
                                color=tema.TEXTO,
                            ),
                            ft.Text(
                                "El jefe de sanidad asignará tus zonas después del registro.",
                                size=13, color=tema.TEXTO_SUAVE,
                            ),
                        ],
                        spacing=6,
                    ),
                    nombre,
                    usuario,
                    ft.ResponsiveRow(
                        [contrasena, repetir], spacing=12, run_spacing=16
                    ),
                    ft.Row([rol]),
                    ft.Text(
                        "Todos los campos son obligatorios.", size=12, color=tema.TEXTO_SUAVE
                    ),
                    mensaje_error,
                    botones,
                ],
                spacing=16, tight=True,
            ),
        )
        responsive = ft.ResponsiveRow(
            [ft.Container(content=tarjeta, col={"xs": 12, "sm": 10, "md": 8, "lg": 6, "xl": 5})],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            spacing=0,
            run_spacing=0,
        )
        return ft.View(
            self.RUTA, [ft.Container(content=responsive, expand=True)], padding=24, bgcolor=tema.FONDO,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
        )
