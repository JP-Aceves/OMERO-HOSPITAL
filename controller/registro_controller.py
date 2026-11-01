"""Responsable: Medina (OME-24)."""
from model.usuario import crear_usuario, hashear
from persistence.repositorio_json import RepositorioJSON


class RegistroController:

    def __init__(self, repositorio: RepositorioJSON) -> None:
        self.repositorio = repositorio

    def registrar(self, nombre: str, usuario: str, contrasena: str, repetir: str, rol: str) -> str | None:
        """Devuelve None si se registró, o el mensaje de error que hay que mostrar."""
        if any(not campo.strip() for campo in (nombre, usuario, contrasena, repetir, rol)):
            return "Rellena todos los campos"
        if contrasena != repetir:
            return "Las contraseñas no coinciden"
        if rol not in ("jefe_sanidad", "responsable_carpa", "tecnico_logistica"):
            return "Selecciona un rol válido"

        sal, contrasena_hash = hashear(contrasena)
        nuevo_usuario = crear_usuario({
            "nombre": nombre.strip(),
            "usuario": usuario.strip(),
            "rol": rol,
            "sal": sal,
            "hash": contrasena_hash,
        })
        try:
            self.repositorio.anadir(nuevo_usuario)
        except ValueError:
            return "Ese usuario ya existe"
        return None
