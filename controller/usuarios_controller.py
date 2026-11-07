"""Gestión de usuarios para el administrador. Responsable: Medina (OME-57)."""
from threading import RLock

from model.lista_enlazada import ListaEnlazada
from model.usuario import Administrador, Usuario, crear_usuario
from persistence.repositorio_json import RepositorioJSON


class UsuariosController:

    def __init__(self, repositorio: RepositorioJSON) -> None:
        self.repositorio = repositorio
        self._operaciones = RLock()

    def listar(self) -> ListaEnlazada:
        with self._operaciones:
            return self.repositorio.cargar()

    def cambiar_rol(self, usuario: str, rol: str) -> str | None:
        """None si va bien, o el mensaje de error."""
        with self._operaciones:
            return self._cambiar_rol(usuario, rol)

    def _cambiar_rol(self, usuario: str, rol: str) -> str | None:
        cuenta = self.repositorio.buscar_por_usuario(usuario)
        if cuenta is None:
            return "El usuario no existe"
        if cuenta.ROL == rol:
            return None

        datos = cuenta.to_dict()
        datos["rol"] = rol
        try:
            nueva_cuenta = crear_usuario(datos)
        except ValueError:
            return "Selecciona un rol válido"

        if cuenta.ROL == Administrador.ROL and not self._hay_otro_administrador(usuario):
            return "Debe quedar al menos un administrador"

        try:
            self.repositorio.actualizar(nueva_cuenta)
        except ValueError:
            return "El usuario no existe"
        return None

    def eliminar(self, usuario: str, actual: Usuario) -> str | None:
        """No deja borrarse a sí mismo ni dejar la app sin ningún administrador."""
        with self._operaciones:
            return self._eliminar(usuario, actual)

    def _eliminar(self, usuario: str, actual: Usuario) -> str | None:
        cuenta_actual = self.repositorio.buscar_por_usuario(actual.usuario)
        if (
            actual.ROL != Administrador.ROL
            or cuenta_actual is None
            or cuenta_actual.ROL != Administrador.ROL
        ):
            return "Solo un administrador puede eliminar usuarios"
        if usuario == actual.usuario:
            return "No puedes eliminar tu propia cuenta"

        cuenta = self.repositorio.buscar_por_usuario(usuario)
        if cuenta is None:
            return "El usuario no existe"
        if cuenta.ROL == Administrador.ROL and not self._hay_otro_administrador(usuario):
            return "Debe quedar al menos un administrador"
        if not self.repositorio.eliminar(usuario):
            return "El usuario no existe"
        return None

    def _hay_otro_administrador(self, usuario: str) -> bool:
        return any(
            cuenta.ROL == Administrador.ROL and cuenta.usuario != usuario
            for cuenta in self.listar()
        )
