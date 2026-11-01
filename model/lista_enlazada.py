"""Lista enlazada propia (el enunciado no permite usar list). Responsable: Ivan (OME-30)."""
from model.nodo import Nodo


class ListaEnlazada:

    def __init__(self) -> None:
        self.cabeza: Nodo | None = None
        self._cola: Nodo | None = None
        self._tamano = 0

    def insertar(self, dato) -> None:
        """Añade el dato al final."""
        nuevo = Nodo(dato)
        if self.cabeza is None:
            self.cabeza = nuevo
        else:
            self._cola.siguiente = nuevo
        self._cola = nuevo
        self._tamano += 1

    def buscar(self, condicion):
        """Devuelve el primer dato que cumple condicion(dato), o None."""
        actual = self.cabeza
        while actual is not None:
            if condicion(actual.dato):
                return actual.dato
            actual = actual.siguiente
        return None

    def eliminar(self, condicion) -> bool:
        """Elimina el primer dato que cumple condicion(dato). True si eliminó algo."""
        anterior = None
        actual = self.cabeza
        while actual is not None:
            if condicion(actual.dato):
                if anterior is None:
                    self.cabeza = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                if actual is self._cola:
                    self._cola = anterior
                self._tamano -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

    def __len__(self) -> int:
        return self._tamano

    def __iter__(self):
        """Permite recorrerla con un for."""
        actual = self.cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente
