"""Qué pantallas ve cada rol y a dónde va tras el login. Responsable: JP (OME-25).

El "/inicio" del jefe de sanidad es su dashboard (OME-40, DashboardJefeView).
"""

MENU_POR_ROL: dict[str, list[tuple[str, str]]] = {
    "administrador": [("Usuarios", "/usuarios")],
    "jefe_sanidad": [("Estado global", "/inicio"), ("Zonas y sensores", "/zonas")],
    "responsable_carpa": [("Mi carpa", "/inicio")],
    "tecnico_logistica": [("Recursos", "/inicio")],
}


def ruta_inicial(rol: str) -> str:
    """Primera ruta del menú del rol."""
    raise NotImplementedError("OME-25")


def puede_acceder(rol: str, ruta: str) -> bool:
    """True si la ruta está en el menú del rol."""
    raise NotImplementedError("OME-25")
