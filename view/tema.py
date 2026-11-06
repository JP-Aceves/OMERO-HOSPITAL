"""Identidad visual de OMERO, compartida por todas las pantallas (OME-36)."""
from __future__ import annotations

import flet as ft

# Colores de los mockups
PANEL = "#2C3E50"
PANEL_ACTIVO = "#0A6CD6"
PRIMARIO = "#0A6CD6"
FONDO = "#F5F7FA"
TARJETA = "#FFFFFF"
BORDE = "#CDD7E2"
TEXTO = "#24364B"
TEXTO_SUAVE = "#60748A"
NORMAL = "#2E7D32"
AVISO = "#B26A00"
CRITICO = "#B42318"
FUENTE_TITULOS = "Clash Display"

# Nombres explícitos para que nuevas vistas puedan usar el tema de forma clara.
COLOR_PANEL = PANEL
COLOR_PRIMARIO = PRIMARIO
COLOR_FONDO = FONDO
COLOR_SUPERFICIE = TARJETA
COLOR_TEXTO = TEXTO
COLOR_TEXTO_SECUNDARIO = TEXTO_SUAVE
COLOR_BORDE = BORDE
COLOR_NORMAL = NORMAL
COLOR_AVISO = AVISO
COLOR_CRITICO = CRITICO
TIPOGRAFIA = FUENTE_TITULOS


def registrar_fuentes(page: ft.Page) -> None:
    """Registra Clash Display desde assets/fonts; llamar al iniciar la página."""
    page.fonts = {**(page.fonts or {}), FUENTE_TITULOS: "fonts/ClashDisplay-Semibold.ttf"}


def boton_primario(texto: str, on_click=None, *, icono: str | None = None, **kwargs) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=texto, icon=icono, on_click=on_click, color=TARJETA, bgcolor=PRIMARIO,
        height=48, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), **kwargs)


def boton_secundario(texto: str, on_click=None, *, icono: str | None = None, **kwargs) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text=texto, icon=icono, on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARIO, side=ft.BorderSide(1, PRIMARIO),
            shape=ft.RoundedRectangleBorder(radius=8)), **kwargs)


def campo_texto(etiqueta: str, **kwargs) -> ft.TextField:
    estilo = {
        "border_radius": 8, "border_color": BORDE, "focused_border_color": PRIMARIO,
        "color": TEXTO, "label_style": ft.TextStyle(color=TEXTO_SUAVE), "text_size": 14,
        "filled": True, "fill_color": TARJETA,
    }
    estilo.update(kwargs)
    return ft.TextField(label=etiqueta, **estilo)


def etiqueta_estado(estado: str, texto: str | None = None) -> ft.Control:
    """Devuelve una etiqueta normal, de aviso o crítica."""
    colores = {"normal": NORMAL, "aviso": AVISO, "critico": CRITICO}
    color = colores[estado]
    return ft.Container(
        content=ft.Text(texto or estado.capitalize(), color=color, size=13, weight=ft.FontWeight.W_600),
        bgcolor=f"{color}1A", padding=ft.padding.symmetric(horizontal=10, vertical=5), border_radius=12)
