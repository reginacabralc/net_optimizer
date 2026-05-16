"""
hash_map.py — HashMap propio con encadenamiento separado.

Implementación manual de tabla hash para demostrar O(1) promedio
en insert, get y delete. Usa encadenamiento separado (listas enlazadas)
para resolver colisiones.

Complejidad:
    put(key, value)  → O(1) amortizado  (O(n) en rehash, raro)
    get(key)         → O(1) promedio    (O(n) peor caso: todas colisionan)
    remove(key)      → O(1) promedio
    contains(key)    → O(1) promedio

Comparación vs búsqueda lineal (list):
    Operación     HashMap    Lista
    insert        O(1)*      O(1)
    search        O(1)*      O(n)   ← ventaja clave
    delete        O(1)*      O(n)
    * amortizado / promedio
"""

from typing import Any, Iterator, List, Optional, Tuple


# Factor de carga máximo antes de hacer rehash
_MAX_LOAD_FACTOR = 0.75
# Capacidad inicial de la tabla (potencia de 2 para mejor distribución)
_INITIAL_CAPACITY = 64


class _Entry:
    """Nodo de la lista enlazada en cada cubeta."""

    __slots__ = ("key", "value", "next_entry")

    def __init__(self, key: str, value: Any, next_entry: Optional["_Entry"] = None):
        self.key = key
        self.value = value
        self.next_entry = next_entry


class HashMap:
    """
    Tabla hash con encadenamiento separado.

    Cada cubeta es el inicio de una lista enlazada de _Entry.
    Cuando el factor de carga supera _MAX_LOAD_FACTOR, la tabla
    se duplica y se rehashean todas las entradas.

    Uso:
        hm = HashMap()
        hm.put("S01", node_object)
        node = hm.get("S01")
        hm.remove("S01")
        "S01" in hm  # → False
    """

    def __init__(self, capacity: int = _INITIAL_CAPACITY) -> None:
        """
        Inicializa la tabla hash.

        Parámetros:
            capacity: Número inicial de cubetas (preferible potencia de 2).
        """
        self._capacity: int = capacity
        self._size: int = 0
        self._buckets: List[Optional[_Entry]] = [None] * self._capacity

    # ── Función hash ────────────────────────────────────────────────────────

    def _hash(self, key: str) -> int:
        """
        Función hash polinomial (variante djb2) para strings.

        h = 5381
        h = h * 33 ^ ord(c)  para cada c en key

        Produce distribución uniforme para strings de nombres de nodos.
        El módulo garantiza índice dentro del rango de cubetas.

        Parámetros:
            key: Clave string a hashear.

        Retorna:
            Índice de cubeta (0 ≤ índice < capacidad).
        """
        h = 5381
        for ch in key:
            h = (h * 33) ^ ord(ch)
        return h % self._capacity

    # ── Operaciones principales ──────────────────────────────────────────────

    def put(self, key: str, value: Any) -> None:
        """
        Inserta o actualiza un par (key, value).

        Si la clave ya existe, actualiza el valor.
        Si el factor de carga supera el umbral, realiza rehash.

        Parámetros:
            key:   Clave string (ej: node_id o nombre de nodo).
            value: Valor a asociar (cualquier objeto).
        """
        if self._load_factor() >= _MAX_LOAD_FACTOR:
            self._rehash()

        idx = self._hash(key)
        entry = self._buckets[idx]

        # Recorrer la cadena buscando la clave
        while entry is not None:
            if entry.key == key:
                entry.value = value  # Actualizar si ya existe
                return
            entry = entry.next_entry

        # Insertar al inicio de la cadena (O(1))
        new_entry = _Entry(key, value, self._buckets[idx])
        self._buckets[idx] = new_entry
        self._size += 1

    def get(self, key: str) -> Any:
        """
        Obtiene el valor asociado a la clave.

        Parámetros:
            key: Clave a buscar.

        Retorna:
            Valor asociado a la clave.

        Raises:
            KeyError: Si la clave no existe.
        """
        idx = self._hash(key)
        entry = self._buckets[idx]
        while entry is not None:
            if entry.key == key:
                return entry.value
            entry = entry.next_entry
        raise KeyError(f"Clave no encontrada: '{key}'")

    def get_or_default(self, key: str, default: Any = None) -> Any:
        """
        Obtiene el valor o devuelve el valor por defecto si la clave no existe.

        Parámetros:
            key:     Clave a buscar.
            default: Valor por defecto si no existe la clave.

        Retorna:
            Valor asociado o valor por defecto.
        """
        try:
            return self.get(key)
        except KeyError:
            return default

    def remove(self, key: str) -> bool:
        """
        Elimina la entrada con la clave dada.

        Parámetros:
            key: Clave a eliminar.

        Retorna:
            True si se eliminó, False si no existía.
        """
        idx = self._hash(key)
        entry = self._buckets[idx]
        prev: Optional[_Entry] = None

        while entry is not None:
            if entry.key == key:
                if prev is None:
                    self._buckets[idx] = entry.next_entry
                else:
                    prev.next_entry = entry.next_entry
                self._size -= 1
                return True
            prev = entry
            entry = entry.next_entry

        return False

    def contains(self, key: str) -> bool:
        """
        Verifica si la clave existe en la tabla.

        Parámetros:
            key: Clave a verificar.

        Retorna:
            True si existe, False si no.
        """
        idx = self._hash(key)
        entry = self._buckets[idx]
        while entry is not None:
            if entry.key == key:
                return True
            entry = entry.next_entry
        return False

    def keys(self) -> List[str]:
        """
        Retorna lista de todas las claves en la tabla.

        Retorna:
            Lista de claves (orden no garantizado).
        """
        result: List[str] = []
        for bucket in self._buckets:
            entry = bucket
            while entry is not None:
                result.append(entry.key)
                entry = entry.next_entry
        return result

    def values(self) -> List[Any]:
        """
        Retorna lista de todos los valores en la tabla.

        Retorna:
            Lista de valores (orden no garantizado).
        """
        result: List[Any] = []
        for bucket in self._buckets:
            entry = bucket
            while entry is not None:
                result.append(entry.value)
                entry = entry.next_entry
        return result

    def items(self) -> List[Tuple[str, Any]]:
        """
        Retorna lista de (key, value) para todas las entradas.

        Retorna:
            Lista de tuplas (key, value).
        """
        result: List[Tuple[str, Any]] = []
        for bucket in self._buckets:
            entry = bucket
            while entry is not None:
                result.append((entry.key, entry.value))
                entry = entry.next_entry
        return result

    # ── Rehash ───────────────────────────────────────────────────────────────

    def _rehash(self) -> None:
        """
        Duplica la capacidad y reinserta todas las entradas.

        Se llama automáticamente cuando load_factor >= _MAX_LOAD_FACTOR.
        Complejidad: O(n) — ocurre raramente (amortizado O(1) por inserción).
        """
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [None] * self._capacity
        self._size = 0  # put() lo incrementará

        for bucket in old_buckets:
            entry = bucket
            while entry is not None:
                self.put(entry.key, entry.value)
                entry = entry.next_entry

    def _load_factor(self) -> float:
        """Retorna el factor de carga actual: size / capacity."""
        return self._size / self._capacity

    # ── Dunder methods ───────────────────────────────────────────────────────

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.put(key, value)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __repr__(self) -> str:
        return (
            f"HashMap(tamaño={self._size}, "
            f"capacidad={self._capacity}, "
            f"carga={self._load_factor():.2f})"
        )

    def stats(self) -> str:
        """
        Retorna estadísticas de la tabla para análisis en demo.

        Retorna:
            Cadena con estadísticas de distribución de cubetas.
        """
        used = sum(1 for b in self._buckets if b is not None)
        max_chain = 0
        total_chain = 0
        for b in self._buckets:
            length = 0
            entry = b
            while entry is not None:
                length += 1
                entry = entry.next_entry
            if length > max_chain:
                max_chain = length
            total_chain += length

        avg_chain = total_chain / used if used > 0 else 0
        return (
            f"Estadísticas HashMap:\n"
            f"  Entradas:      {self._size}\n"
            f"  Capacidad:     {self._capacity}\n"
            f"  Factor de carga: {self._load_factor():.3f}\n"
            f"  Cubetas usadas:{used}/{self._capacity}\n"
            f"  Cadena máxima: {max_chain}\n"
            f"  Cadena promedio: {avg_chain:.2f}"
        )
