"""Panel lateral del mockup, común a todas las pantallas tras el login. Responsable: JP (OME-25).

Estructura (mockups 03 y 06):

    View
    └── Row
        ├── panel lateral (logo · menú del rol · usuario y cerrar sesión)
        └── contenido (la pantalla que toque: dashboard, zonas, usuarios...)

La vista no decide nada: el menú sale de navegacion.MENU_POR_ROL y al pulsar
una opción solo avisa a main.py con on_navegar(ruta).
"""
from typing import Callable

import flet as ft

from controller.navegacion import MENU_POR_ROL
from model.usuario import Usuario
from view import tema

NOMBRE_ROL = {
    "administrador": "Administrador",
    "jefe_sanidad": "Jefe de sanidad",
    "responsable_carpa": "Responsable de carpa",
    "tecnico_logistica": "Técnico de logística",
}

ICONO_RUTA = {
    "/inicio": ft.Icons.DASHBOARD_OUTLINED,
    "/zonas": ft.Icons.MAP_OUTLINED,
    "/usuarios": ft.Icons.PEOPLE_OUTLINE,
}

ANCHO_PANEL = 260
ANCHO_PANEL_COMPACTO = 76


class ShellView:

    def __init__(self, usuario: Usuario, ruta_actual: str, contenido: ft.Control,
                 on_navegar: Callable[[str], None], on_cerrar_sesion: Callable[[], None],
                 compacto: bool = False) -> None:
        """compacto=True con la ventana estrecha: el panel solo enseña iconos."""
        self.usuario = usuario
        self.ruta_actual = ruta_actual
        self.contenido = contenido
        self.on_navegar = on_navegar
        self.on_cerrar_sesion = on_cerrar_sesion
        self.compacto = compacto

    def construir(self) -> ft.View:
        return ft.View(
            self.ruta_actual,
            [
                ft.Row(
                    [self._panel(), self._zona_contenido()],
                    expand=True,
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                )
            ],
            padding=0,
            bgcolor=tema.FONDO,
        )

    # ---------- panel lateral ----------

    def _panel(self) -> ft.Control:
        menu = [self._opcion(titulo, ruta) for titulo, ruta in MENU_POR_ROL.get(self.usuario.ROL, [])]
        return ft.Container(
            width=ANCHO_PANEL_COMPACTO if self.compacto else ANCHO_PANEL,
            bgcolor=tema.PANEL,
            padding=ft.padding.symmetric(horizontal=12, vertical=24),
            content=ft.Column(
                [self._logo(), ft.Container(height=24), *menu, ft.Container(expand=True), self._pie()],
                spacing=6,
            ),
        )

    def _logo(self) -> ft.Control:
        icono = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=tema.PRIMARIO, size=30)
        if self.compacto:
            return ft.Row([icono], alignment=ft.MainAxisAlignment.CENTER)
        texto = ft.Text("OMERO", size=22, weight=ft.FontWeight.BOLD, color="#FFFFFF",
                        font_family=tema.FUENTE_TITULOS)
        return ft.Row([icono, texto], spacing=10)

    def _opcion(self, titulo: str, ruta: str) -> ft.Control:
        activa = ruta == self.ruta_actual
        icono = ft.Icon(ICONO_RUTA.get(ruta, ft.Icons.CIRCLE), color="#FFFFFF", size=20)
        if self.compacto:
            fila = ft.Row([icono], alignment=ft.MainAxisAlignment.CENTER)
        else:
            fila = ft.Row([icono, ft.Text(titulo, color="#FFFFFF", size=15)], spacing=12)
        return ft.Container(
            content=fila,
            bgcolor=tema.PANEL_ACTIVO if activa else None,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            tooltip=titulo if self.compacto else None,
            # r=ruta: guarda la ruta de ESTA opción (si no, todas usarían la última)
            on_click=lambda _evento, r=ruta: self.on_navegar(r),
        )

    def _pie(self) -> ft.Control:
        salir = ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color="#9CC4F2", size=18)]
                           + ([] if self.compacto else [ft.Text("Cerrar sesión", color="#9CC4F2")]),
                           spacing=8),
            on_click=lambda _evento: self.on_cerrar_sesion(),
            tooltip="Cerrar sesión" if self.compacto else None,
        )
        if self.compacto:
            return ft.Column([salir], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        return ft.Column(
            [
                ft.Divider(color="#46586B"),
                ft.Text(self.usuario.nombre, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                ft.Text(NOMBRE_ROL.get(self.usuario.ROL, self.usuario.ROL), color="#B8C4D0", size=13),
                salir,
            ],
            spacing=4,
        )

    # ---------- contenido ----------

    def _zona_contenido(self) -> ft.Control:
        return ft.Container(
            content=ft.Column([self.contenido], scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
            padding=32,
        )
