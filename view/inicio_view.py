"""Pantalla de inicio del responsable de carpa y del técnico de logística. Responsable: JP (OME-25).

Saluda al usuario y le enseña SUS zonas (HU-04): las pide al ZonasController,
que solo devuelve las que tiene asignadas. El jefe de sanidad no usa esta
pantalla: su inicio es el dashboard (OME-40).
"""
import flet as ft

from controller.zonas_controller import ZonasController
from model.usuario import Usuario
from view import tema
from view.zonas_view import resumen_zona

NOMBRE_TIPO = {"carpa": "Carpa", "zona_tecnica": "Zona técnica", "exterior": "Exterior"}


class InicioView:

    def __init__(self, usuario: Usuario, zonas: ZonasController) -> None:
        self.usuario = usuario
        self.zonas = zonas

    def construir(self) -> ft.Control:
        mis_zonas = self.zonas.listar(self.usuario)
        tarjetas = [self._tarjeta(zona) for zona in mis_zonas]
        if not tarjetas:
            tarjetas = [ft.Text("Todavía no tienes zonas asignadas.", color=tema.TEXTO_SUAVE)]
        return ft.Column(
            [
                ft.Text(f"Hola, {self.usuario.nombre}", size=30, weight=ft.FontWeight.BOLD,
                        color=tema.TEXTO, font_family=tema.FUENTE_TITULOS),
                ft.Text(f"Tus zonas asignadas: {len(mis_zonas)}", color=tema.TEXTO_SUAVE),
                ft.Container(height=12),
                # ResponsiveRow: 3 tarjetas por fila en pantalla grande, 1 en estrecha
                ft.ResponsiveRow(tarjetas, spacing=16, run_spacing=16),
            ],
            spacing=6,
        )

    def _tarjeta(self, zona) -> ft.Control:
        return ft.Container(
            col={"xs": 12, "md": 6, "lg": 4},
            bgcolor=tema.TARJETA,
            border=ft.border.all(1, tema.BORDE),
            border_radius=14,
            padding=20,
            content=ft.Column(
                [
                    ft.Text(zona.nombre, size=18, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
                    ft.Text(NOMBRE_TIPO.get(zona.tipo, zona.tipo), color=tema.TEXTO_SUAVE),
                    ft.Text(resumen_zona(zona), color=tema.TEXTO_SUAVE, size=13),
                ],
                spacing=4,
            ),
        )
