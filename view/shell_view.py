"""Panel lateral del mockup, común a todas las pantallas tras el login. Responsable: JP (OME-25)."""
from typing import Callable

import flet as ft

from model.usuario import Usuario


class ShellView:

    def __init__(self, usuario: Usuario, ruta_actual: str, contenido: ft.Control,
                 on_navegar: Callable[[str], None], on_cerrar_sesion: Callable[[], None]) -> None:
        raise NotImplementedError("OME-25")

    def construir(self) -> ft.View:
        raise NotImplementedError("OME-25")
