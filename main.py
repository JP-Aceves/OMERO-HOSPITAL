"""Punto de entrada de OMERO · Monitor de hospital de campaña.

Solo JP modifica este archivo (OME-25). Aquí no hay lógica: crea los
controladores, decide qué pantalla toca según la ruta y mete cada pantalla
dentro del panel lateral (ShellView).
"""
import flet as ft

from controller import navegacion
from controller.dashboard_controller import DashboardController
from controller.login_controller import LoginController
from controller.registro_controller import RegistroController
from controller.usuarios_controller import UsuariosController
from controller.zonas_controller import ZonasController
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador
from view import tema
from view.dashboard_jefe_view import DashboardJefeView
from view.inicio_view import InicioView
from view.login_view import LoginView
from view.registro_view import RegistroView
from view.shell_view import ShellView
from view.tema import registrar_fuentes
from view.usuarios_view import UsuariosView
from view.zonas_view import ZonasView

ANCHO_COMPACTO = 900  # por debajo, el panel lateral solo enseña iconos


def pendiente(tarea: str) -> ft.Control:
    """Lo que se ve mientras la pantalla de un compañero no está mergeada."""
    return ft.Column([
        ft.Icon(ft.Icons.CONSTRUCTION, color=tema.TEXTO_SUAVE, size=40),
        ft.Text(f"Pantalla en construcción ({tarea})", size=18, color=tema.TEXTO_SUAVE),
    ])


def main(page: ft.Page) -> None:
    page.title = "OMERO"
    page.theme_mode = ft.ThemeMode.LIGHT
    # Sin animación al cambiar de pantalla (en Mac se deslizaba de lado)
    sin_transicion = ft.PageTransitionsTheme(
        macos=ft.PageTransitionTheme.NONE,
        windows=ft.PageTransitionTheme.NONE,
        linux=ft.PageTransitionTheme.NONE,
    )
    page.theme = ft.Theme(page_transitions=sin_transicion)
    page.window.width = 1280
    page.window.height = 760
    page.window.min_width = 700
    page.window.min_height = 500
    registrar_fuentes(page)  # Clash Display (OME-36)

    repositorio = RepositorioJSON()
    login = LoginController(repositorio)
    registro = RegistroController(repositorio)
    sesion = {"usuario": None, "compacto": False}

    # ---------- qué hay dentro de cada ruta ----------

    def contenido_inicio(usuario):
        if usuario.ROL == "jefe_sanidad":
            dashboard = DashboardController(RepositorioZonas(), RepositorioLecturas(),
                                            Simulador(RepositorioZonas(), RepositorioLecturas()))
            return DashboardJefeView(usuario, dashboard).construir()
        return InicioView(usuario, ZonasController(RepositorioZonas(), repositorio)).construir()

    def contenido_zonas(usuario):
        return ZonasView(usuario, ZonasController(RepositorioZonas(), repositorio)).construir()

    def contenido_usuarios(usuario):
        return UsuariosView(usuario, UsuariosController(repositorio)).construir()

    PANTALLAS = {
        "/inicio": (contenido_inicio, "OME-40 / OME-32"),
        "/zonas": (contenido_zonas, "OME-35"),
        "/usuarios": (contenido_usuarios, "OME-57"),
    }

    def construir_contenido(ruta, usuario):
        construir, tarea = PANTALLAS[ruta]
        try:
            return construir(usuario)
        except NotImplementedError:
            # Mientras un compañero no termine su parte, la app no se rompe
            return pendiente(tarea)

    # ---------- callbacks que reciben las vistas ----------

    def al_entrar(usuario, contrasena):
        encontrado = login.login(usuario, contrasena)
        if encontrado is None:
            return "Usuario o contraseña incorrectos"
        sesion["usuario"] = encontrado
        page.go(navegacion.ruta_inicial(encontrado.ROL))
        return None

    def al_registrar(nombre, usuario, contrasena, repetir, rol):
        error = registro.registrar(nombre, usuario, contrasena, repetir, rol)
        if error is None:
            page.go("/login")
        return error

    def cerrar_sesion():
        sesion["usuario"] = None
        page.go("/login")

    # ---------- router ----------

    def ruta_cambiada(_evento=None):
        usuario = sesion["usuario"]
        ruta = page.route
        page.views.clear()

        if usuario is None:
            if ruta == "/registro":
                page.views.append(RegistroView(al_registrar, lambda: page.go("/login")).construir())
            else:
                page.views.append(LoginView(al_entrar, lambda: page.go("/registro")).construir())
            page.update()
            return

        # Con sesión: si la ruta no es suya, a su inicio
        if not navegacion.puede_acceder(usuario.ROL, ruta):
            page.go(navegacion.ruta_inicial(usuario.ROL))
            return

        page.views.append(ShellView(
            usuario, ruta, construir_contenido(ruta, usuario),
            on_navegar=page.go, on_cerrar_sesion=cerrar_sesion,
            compacto=sesion["compacto"],
        ).construir())
        page.update()

    def ventana_cambiada(_evento=None):
        # Solo se repinta si cambia de grande a estrecha o al revés
        compacto = (page.width or 1280) < ANCHO_COMPACTO
        if compacto != sesion["compacto"]:
            sesion["compacto"] = compacto
            ruta_cambiada()

    page.on_route_change = ruta_cambiada
    page.on_resized = ventana_cambiada
    page.go("/login")


if __name__ == "__main__":
    ft.app(target=main)
