"""CRUD de zonas, sensores y actuadores y asignación de responsable. Responsable: Rodas (OME-32).

Igual que RegistroController: cada método devuelve None si va bien o el mensaje de error.
"""
from model.lista_enlazada import ListaEnlazada
from model.usuario import Usuario
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_zonas import RepositorioZonas


class ZonasController:

    def __init__(self, repo_zonas: RepositorioZonas, repo_usuarios: RepositorioJSON) -> None:
        raise NotImplementedError("OME-32")

    def listar(self, usuario: Usuario) -> ListaEnlazada:
        """Jefe de sanidad: todas. Responsable de carpa y técnico: solo las suyas."""
        raise NotImplementedError("OME-32")

    def crear_zona(self, nombre: str, tipo: str, responsable: str | None) -> str | None:
        raise NotImplementedError("OME-32")

    def editar_zona(self, id_zona: str, nombre: str, tipo: str, responsable: str | None) -> str | None:
        raise NotImplementedError("OME-32")

    def eliminar_zona(self, id_zona: str) -> str | None:
        raise NotImplementedError("OME-32")

    def anadir_sensor(self, id_zona: str, nombre: str, tipo: str, umbral_aviso: str, umbral_critico: str) -> str | None:
        """Los umbrales llegan como texto desde la vista: si no son números, devuelve el error."""
        raise NotImplementedError("OME-32")

    def editar_sensor(self, id_zona: str, id_sensor: str, nombre: str, umbral_aviso: str, umbral_critico: str) -> str | None:
        raise NotImplementedError("OME-32")

    def eliminar_sensor(self, id_zona: str, id_sensor: str) -> str | None:
        raise NotImplementedError("OME-32")

    def anadir_actuador(self, id_zona: str, nombre: str, tipo: str) -> str | None:
        raise NotImplementedError("OME-32")

    def eliminar_actuador(self, id_zona: str, id_actuador: str) -> str | None:
        raise NotImplementedError("OME-32")

    def asignar_responsable(self, id_zona: str, usuario: str) -> str | None:
        """Solo usuarios con rol responsable_carpa o tecnico_logistica."""
        raise NotImplementedError("OME-32")

    def responsables_disponibles(self) -> ListaEnlazada:
        """Usuarios que se pueden asignar a una zona (para el desplegable)."""
        raise NotImplementedError("OME-32")
