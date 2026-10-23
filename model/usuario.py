"""Usuarios de OMERO. Responsable: Medina (OME-21)."""
from abc import ABC


def hashear(contrasena: str, sal: str | None = None) -> tuple[str, str]:
    """Devuelve (sal, hash) en hexadecimal. Si no se pasa sal, genera una nueva."""
    raise NotImplementedError("OME-21")


class Usuario(ABC):
    """Usuario abstracto. Cada rol es una subclase."""

    ROL = ""

    def __init__(self, nombre: str, usuario: str, contrasena_hash: str, sal: str) -> None:
        self.nombre = nombre
        self.usuario = usuario
        self.contrasena_hash = contrasena_hash
        self.sal = sal

    def verificar_password(self, contrasena: str) -> bool:
        raise NotImplementedError("OME-21")

    def to_dict(self) -> dict:
        """{"nombre", "usuario", "rol", "sal", "hash"} para guardar en el JSON."""
        raise NotImplementedError("OME-21")


class JefeSanidad(Usuario):
    ROL = "jefe_sanidad"


class ResponsableCarpa(Usuario):
    ROL = "responsable_carpa"


class TecnicoLogistica(Usuario):
    ROL = "tecnico_logistica"


def crear_usuario(datos: dict) -> Usuario:
    """Crea la subclase correcta a partir de un dict leído del JSON."""
    raise NotImplementedError("OME-21")
