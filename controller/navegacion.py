"""Qué pantallas ve cada rol y a dónde va tras el login. Responsable: JP (OME-25).

El "/inicio" del jefe de sanidad es su dashboard (OME-40, DashboardJefeView).
MENU_POR_ROL es configuración fija, no datos de la app: por eso puede ser dict y list.
"""

MENU_POR_ROL: dict[str, list[tuple[str, str]]] = {
    "administrador": [("Usuarios", "/usuarios")],
    "jefe_sanidad": [("Estado global", "/inicio"), ("Zonas y sensores", "/zonas")],
    "responsable_carpa": [("Mi carpa", "/inicio")],
    "tecnico_logistica": [("Recursos", "/inicio")],
}


def ruta_inicial(rol: str) -> str:
    """Primera ruta del menú del rol. Si el rol no existe, vuelve al login."""
    menu = MENU_POR_ROL.get(rol)
    if not menu:
        return "/login"
    _, ruta = menu[0]
    return ruta


def puede_acceder(rol: str, ruta: str) -> bool:
    """True si la ruta está en el menú del rol."""
    for _, ruta_menu in MENU_POR_ROL.get(rol, []):
        if ruta_menu == ruta:
            return True
    return False
