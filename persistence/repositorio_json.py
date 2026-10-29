"""Lectura y escritura de usuarios en JSON. Responsable: Ivan (OME-22)."""
import json
from pathlib import Path

from model.lista_enlazada import ListaEnlazada
from model.usuario import Usuario, crear_usuario


class RepositorioJSON:

    def __init__(self, ruta: Path = Path("data/usuarios.json")) -> None:
        self.ruta = Path(ruta)
        self._usuarios = self.cargar()

    def cargar(self) -> ListaEnlazada:
        """Lee el JSON y devuelve una ListaEnlazada de Usuario."""
        usuarios = ListaEnlazada()
        if self.ruta.exists():
            with self.ruta.open(encoding="utf-8") as fichero:
                for datos in json.load(fichero):
                    usuarios.insertar(crear_usuario(datos))
        return usuarios

    def guardar(self, usuarios: ListaEnlazada) -> None:
        """Escribe todos los usuarios en el JSON, sustituyendo lo que hubiera."""
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        # json solo sabe escribir un array a partir de una list: la creamos
        # aquí, justo al escribir, y no la usamos para guardar datos.
        datos = [usuario.to_dict() for usuario in usuarios]
        with self.ruta.open("w", encoding="utf-8") as fichero:
            json.dump(datos, fichero, ensure_ascii=False, indent=2)
        self._usuarios = usuarios

    def buscar_por_usuario(self, nombre_usuario: str) -> Usuario | None:
        raise NotImplementedError("OME-22")

    def anadir(self, usuario: Usuario) -> None:
        """Guarda un usuario nuevo. Lanza ValueError si el nombre de usuario ya existe."""
        raise NotImplementedError("OME-22")