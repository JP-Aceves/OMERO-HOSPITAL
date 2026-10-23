"""Lista enlazada propia (el enunciado no permite usar list). Responsable: Ivan (OME-30)."""
from model.nodo import Nodo


class ListaEnlazada:

    def __init__(self) -> None:
        self.cabeza: Nodo | None = None

    def insertar(self, dato) -> None:
        """Añade el dato al final."""
        raise NotImplementedError("OME-30")

    def buscar(self, condicion):
        """Devuelve el primer dato que cumple condicion(dato), o None."""
        raise NotImplementedError("OME-30")

    def eliminar(self, condicion) -> bool:
        """Elimina el primer dato que cumple condicion(dato). True si eliminó algo."""
        raise NotImplementedError("OME-30")

    def __len__(self) -> int:
        raise NotImplementedError("OME-30")

    def __iter__(self):
        """Permite recorrerla con un for."""
        raise NotImplementedError("OME-30")
