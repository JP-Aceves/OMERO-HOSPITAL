"""Nodo de la lista enlazada. Responsable: Ivan (OME-30)."""


class Nodo:
    """Guarda un dato y apunta al siguiente nodo."""

    def __init__(self, dato) -> None:
        self.dato = dato
        self.siguiente: "Nodo | None" = None
