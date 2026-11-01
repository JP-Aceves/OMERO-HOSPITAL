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
        estilo_campo = {
            "border_radius": 8,
            "border_color": "#CDD7E2",
            "focused_border_color": "#006ED3",
            "color": "#24364B",
            "label_style": ft.TextStyle(color="#60748A"),
            "text_size": 14,
            "filled": True,
            "fill_color": "#FFFFFF",
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
            "", key="test:registro_error", color="#B42318", size=13, visible=False
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
                        color="#006ED3", side=ft.BorderSide(1, "#006ED3"),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
                ft.ElevatedButton(
                    "Registrarme", key="test:registro_enviar", on_click=registrar,
                    height=44, col={"xs": 12, "sm": 6},
                    style=ft.ButtonStyle(
                        color="#FFFFFF", bgcolor="#006ED3", elevation=0,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
            spacing=12, run_spacing=12,
        )
        tarjeta = ft.Container(
            width=640, padding=28, bgcolor="#FFFFFF",
            border=ft.border.all(1, "#DFE6EE"), border_radius=16,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.DONUT_LARGE, color="#009BDA", size=26),
                            ft.Text(
                                "OMERO", size=18, weight=ft.FontWeight.BOLD,
                                color="#24364B",
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "Crear cuenta", size=26, weight=ft.FontWeight.BOLD,
                                color="#24364B",
                            ),
                            ft.Text(
                                "El jefe de sanidad asignará tus zonas después del registro.",
                                size=13, color="#60748A",
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
                        "Todos los campos son obligatorios.", size=12, color="#60748A"
                    ),
                    mensaje_error,
                    botones,
                ],
                spacing=16, tight=True,
            ),
        )
        return ft.View(
            self.RUTA, [tarjeta], padding=24, bgcolor="#F3F6FA",
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
        )
