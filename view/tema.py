"""Identidad visual de OMERO, compartida por todas las pantallas. Responsable: Rodas (OME-36).

Los colores salen de los mockups. Rodas los ajusta con el archivo original de la identidad
y añade la fuente y los componentes reutilizables. Nadie pone colores a mano en su vista:
siempre desde aquí.
"""
import flet as ft

# Colores
PANEL = "#2C3E50"           # panel lateral
PANEL_ACTIVO = "#0A6CD6"    # opción seleccionada del menú
PRIMARIO = "#0A6CD6"        # botones principales
FONDO = "#F5F7FA"           # fondo de las pantallas
TARJETA = "#FFFFFF"
BORDE = "#CDD7E2"
TEXTO = "#24364B"
TEXTO_SUAVE = "#60748A"

# Estados (semáforo)
NORMAL = "#2E7D32"
AVISO = "#B26A00"
CRITICO = "#B42318"

# Tipografía
FUENTE_TITULOS = "Clash Display"


def boton_primario(texto: str, on_click=None) -> ft.Control:
    raise NotImplementedError("OME-36")


def boton_secundario(texto: str, on_click=None) -> ft.Control:
    raise NotImplementedError("OME-36")


def campo_texto(etiqueta: str, **kwargs) -> ft.TextField:
    raise NotImplementedError("OME-36")


def etiqueta_estado(estado: str) -> ft.Control:
    """estado: "normal", "aviso" o "critico"."""
    raise NotImplementedError("OME-36")
