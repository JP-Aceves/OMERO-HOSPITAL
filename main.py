"""Punto de entrada de OMERO · Monitor de hospital de campaña.

Solo JP modifica este archivo (OME-25). Aquí no hay lógica: crea los
controladores, decide qué pantalla toca según la ruta y mete cada pantalla
dentro del panel lateral (ShellView).

OME-71: los sensores se leen solos cada INTERVALO_LECTURAS segundos mientras hay
una sesión de jefe, carpa o técnico, y la pantalla abierta se refresca sola.
"""
import asyncio
import traceback

import flet as ft

from controller import navegacion
from controller.actuadores_controller import ActuadoresController
from controller.carpa_controller import CarpaController
from controller.dashboard_controller import DashboardController
from controller.historico_controller import HistoricoController
from controller.login_controller import LoginController
from controller.registro_controller import RegistroController
from controller.tecnico_controller import TecnicoController
from controller.usuarios_controller import UsuariosController
from controller.zonas_controller import ZonasController
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador
from view import tema
from view.dashboard_carpa_view import DashboardCarpaView
from view.dashboard_jefe_view import DashboardJefeView
from view.dashboard_tecnico_view import DashboardTecnicoView
from view.historico_view import HistoricoView
from view.inicio_view import InicioView
from view.login_view import LoginView
from view.pendiente_view import PendienteView
from view.registro_view import RegistroView
from view.shell_view import ShellView
from view.tema import registrar_fuentes
from view.usuarios_view import UsuariosView
from view.zonas_view import ZonasView

ANCHO_COMPACTO = 900  # por debajo, el panel lateral solo enseña iconos
INTERVALO_LECTURAS = 5  # segundos entre una ronda de lecturas y la siguiente (OME-71)
ROLES_CON_LECTURAS = ("jefe_sanidad", "responsable_carpa", "tecnico_logistica")


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
    # Calendario del histórico en español (OME-71)
    espanol = ft.Locale("es", "ES")
    page.locale_configuration = ft.LocaleConfiguration(supported_locales=[espanol], current_locale=espanol)

    repositorio = RepositorioJSON()
    login = LoginController(repositorio)
    registro = RegistroController(repositorio)
    # "vista": la pantalla abierta, para refrescarla cuando llegan lecturas nuevas
    sesion = {"usuario": None, "compacto": False, "vista": None}

    # OME-71: un solo lector para toda la app. Todas las pantallas comparten sus
    # lecturas en memoria, así ninguna pisa el fichero de otra al guardar.
    lecturas = RepositorioLecturas()
    zonas_lector = RepositorioZonas()
    lector = DashboardController(zonas_lector, lecturas, Simulador(zonas_lector, lecturas))

    # ---------- qué hay dentro de cada ruta ----------

    def abrir(vista):
        """Guarda la pantalla abierta y devuelve su contenido."""
        sesion["vista"] = vista
        return vista.construir()

    def contenido_inicio(usuario):
        if usuario.ROL == "jefe_sanidad":
            return abrir(DashboardJefeView(usuario, lector))
        try:
            if usuario.ROL == "responsable_carpa":  # OME-62
                carpa = CarpaController(lector, ActuadoresController(zonas_lector))
                return abrir(DashboardCarpaView(usuario, carpa))
            if usuario.ROL == "tecnico_logistica":  # OME-63
                tecnico = TecnicoController(lector, ActuadoresController(zonas_lector), lecturas)
                return abrir(DashboardTecnicoView(usuario, tecnico))
        except NotImplementedError:
            pass  # hasta que su dashboard esté mergeado, sigue el inicio del Sprint 2
        return InicioView(
            usuario, ZonasController(RepositorioZonas(), repositorio),
            dashboard=lector,
        ).construir()

    def contenido_pendiente(usuario):
        return PendienteView(usuario).construir()  # OME-61

    def contenido_zonas(usuario):
        return ZonasView(usuario, ZonasController(RepositorioZonas(), repositorio)).construir()

    def contenido_usuarios(usuario):
        return UsuariosView(usuario, UsuariosController(repositorio)).construir()

    def contenido_historico(usuario):
        return abrir(HistoricoView(usuario, HistoricoController(RepositorioZonas(), lecturas)))

    PANTALLAS = {
        "/inicio": (contenido_inicio, "OME-40"),
        "/zonas": (contenido_zonas, "OME-35"),
        "/usuarios": (contenido_usuarios, "OME-57"),
        "/pendiente": (contenido_pendiente, "OME-61"),
        "/historico": (contenido_historico, "OME-70"),
    }

    def construir_contenido(ruta, usuario):
        construir, tarea = PANTALLAS[ruta]
        sesion["vista"] = None
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
        sesion["vista"] = None
        page.go("/login")

    # ---------- lecturas en directo (OME-71) ----------

    async def leer_sensores():
        """Cada INTERVALO_LECTURAS segundos: ronda nueva y refresco de la pantalla abierta."""
        while True:
            await asyncio.sleep(INTERVALO_LECTURAS)
            usuario = sesion["usuario"]
            if usuario is None or usuario.ROL not in ROLES_CON_LECTURAS:
                continue
            try:
                lector.actualizar()
                refrescar = getattr(sesion["vista"], "refrescar", None)
                if refrescar is not None:
                    refrescar()
            except Exception:  # noqa: BLE001 · si una ronda falla, la siguiente lo vuelve a intentar
                traceback.print_exc()

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
    page.run_task(leer_sensores)
    page.go("/login")


if __name__ == "__main__":
    ft.app(target=main)
