"""Gestión de usuarios para el administrador. Responsable: Medina (OME-57)."""
from model.lista_enlazada import ListaEnlazada
from model.usuario import Usuario
from persistence.repositorio_json import RepositorioJSON


class UsuariosController:

    def __init__(self, repositorio: RepositorioJSON) -> None:
        raise NotImplementedError("OME-57")

    def listar(self) -> ListaEnlazada:
        raise NotImplementedError("OME-57")

    def cambiar_rol(self, usuario: str, rol: str) -> str | None:
        """None si va bien, o el mensaje de error."""
        raise NotImplementedError("OME-57")

    def eliminar(self, usuario: str, actual: Usuario) -> str | None:
        """No deja borrarse a sí mismo ni dejar la app sin ningún administrador."""
        raise NotImplementedError("OME-57")
