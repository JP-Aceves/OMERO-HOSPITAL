"""Usuarios de OMERO. Responsable: Medina (OME-21)."""
from abc import ABC, abstractmethod
import hashlib
import secrets


def hashear(contrasena: str, sal: str | None = None) -> tuple[str, str]:
    """Devuelve (sal, hash) en hexadecimal. Si no se pasa sal, genera una nueva."""
    if sal is None:
        sal = secrets.token_hex(16)
    contrasena_hash = hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode(), bytes.fromhex(sal), 100_000
    )
    return sal, contrasena_hash.hex()


class Usuario(ABC):
    """Usuario abstracto. Cada rol es una subclase."""

    @property
    @abstractmethod
    def ROL(self) -> str:
        """Identificador del rol que debe definir cada subclase."""

    def __init__(self, nombre: str, usuario: str, contrasena_hash: str, sal: str) -> None:
        self.nombre = nombre
        self.usuario = usuario
        self.contrasena_hash = contrasena_hash
        self.sal = sal

    def verificar_password(self, contrasena: str) -> bool:
        _, contrasena_hash = hashear(contrasena, self.sal)
        return secrets.compare_digest(contrasena_hash, self.contrasena_hash)

    def to_dict(self) -> dict:
        """{"nombre", "usuario", "rol", "sal", "hash"} para guardar en el JSON."""
        return {
            "nombre": self.nombre,
            "usuario": self.usuario,
            "rol": self.ROL,
            "sal": self.sal,
            "hash": self.contrasena_hash,
        }


class JefeSanidad(Usuario):
    ROL = "jefe_sanidad"


class ResponsableCarpa(Usuario):
    ROL = "responsable_carpa"


class TecnicoLogistica(Usuario):
    ROL = "tecnico_logistica"


def crear_usuario(datos: dict) -> Usuario:
    """Crea la subclase correcta a partir de un dict leído del JSON."""
    roles = {
        "jefe_sanidad": JefeSanidad,
        "responsable_carpa": ResponsableCarpa,
        "tecnico_logistica": TecnicoLogistica,
    }
    clase_usuario = roles.get(datos["rol"])
    if clase_usuario is None:
        raise ValueError(f"Rol de usuario desconocido: {datos['rol']}")
    return clase_usuario(
        nombre=datos["nombre"],
        usuario=datos["usuario"],
        contrasena_hash=datos["hash"],
        sal=datos["sal"],
    )
