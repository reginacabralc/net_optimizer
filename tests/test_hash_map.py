"""
tests/test_hash_map.py — Tests unitarios para HashMap.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.hash_map import HashMap


class TestHashMapBasic:
    """Tests básicos de inserción y recuperación."""

    def test_put_and_get(self):
        hm = HashMap()
        hm.put("clave1", 42)
        assert hm.get("clave1") == 42

    def test_put_and_get_string_value(self):
        hm = HashMap()
        hm.put("nombre", "NetOptimizer")
        assert hm.get("nombre") == "NetOptimizer"

    def test_put_updates_existing_key(self):
        hm = HashMap()
        hm.put("k", 1)
        hm.put("k", 99)
        assert hm.get("k") == 99

    def test_get_missing_key_raises(self):
        hm = HashMap()
        with pytest.raises(KeyError):
            hm.get("no_existe")

    def test_get_or_default_returns_default(self):
        hm = HashMap()
        assert hm.get_or_default("no_existe", "default_val") == "default_val"

    def test_get_or_default_returns_value_if_exists(self):
        hm = HashMap()
        hm.put("k", 7)
        assert hm.get_or_default("k", 0) == 7


class TestHashMapContains:
    """Tests para contains y operador in."""

    def test_contains_existing_key(self):
        hm = HashMap()
        hm.put("router1", "R01")
        assert hm.contains("router1") is True

    def test_contains_missing_key(self):
        hm = HashMap()
        assert hm.contains("no_existe") is False

    def test_in_operator(self):
        hm = HashMap()
        hm.put("server", "S01")
        assert "server" in hm
        assert "otro" not in hm


class TestHashMapRemove:
    """Tests para eliminación."""

    def test_remove_existing_key(self):
        hm = HashMap()
        hm.put("k", 1)
        result = hm.remove("k")
        assert result is True
        assert not hm.contains("k")

    def test_remove_missing_key_returns_false(self):
        hm = HashMap()
        assert hm.remove("no_existe") is False

    def test_size_decreases_after_remove(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        hm.remove("a")
        assert len(hm) == 1


class TestHashMapSize:
    """Tests de tamaño."""

    def test_empty_map_size(self):
        assert len(HashMap()) == 0

    def test_size_after_insertions(self):
        hm = HashMap()
        for i in range(10):
            hm.put(f"key{i}", i)
        assert len(hm) == 10

    def test_size_does_not_increase_on_update(self):
        hm = HashMap()
        hm.put("k", 1)
        hm.put("k", 2)
        assert len(hm) == 1


class TestHashMapKeys:
    """Tests para keys(), values(), items()."""

    def test_keys_returns_all_keys(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        hm.put("c", 3)
        assert sorted(hm.keys()) == ["a", "b", "c"]

    def test_values_returns_all_values(self):
        hm = HashMap()
        hm.put("x", 10)
        hm.put("y", 20)
        assert sorted(hm.values()) == [10, 20]

    def test_items_returns_key_value_pairs(self):
        hm = HashMap()
        hm.put("p", 100)
        hm.put("q", 200)
        items = dict(hm.items())
        assert items == {"p": 100, "q": 200}


class TestHashMapRehash:
    """Tests de rehashing automático."""

    def test_rehash_preserves_data(self):
        """Insertar suficientes elementos para provocar rehash y verificar datos."""
        hm = HashMap(capacity=8)  # Pequeña para forzar rehash pronto
        n = 20
        for i in range(n):
            hm.put(f"nodo_{i:03d}", i * 10)

        # Todos los valores deben seguir accesibles después del rehash
        for i in range(n):
            assert hm.get(f"nodo_{i:03d}") == i * 10

    def test_size_after_many_insertions(self):
        hm = HashMap(capacity=4)
        for i in range(50):
            hm.put(f"k{i}", i)
        assert len(hm) == 50


class TestHashMapCollisions:
    """Tests de manejo de colisiones."""

    def test_collision_separate_chaining(self):
        """
        Claves que colisionan en el mismo bucket deben coexistir.
        Usamos un HashMap pequeño para forzar colisiones.
        """
        hm = HashMap(capacity=2)  # Solo 2 buckets → muchas colisiones
        hm.put("servidor_central", "S01")
        hm.put("servidor_norte", "S02")
        hm.put("servidor_sur", "S03")
        hm.put("router_reforma", "R01")

        # Todos deben ser recuperables
        assert hm.get("servidor_central") == "S01"
        assert hm.get("servidor_norte") == "S02"
        assert hm.get("servidor_sur") == "S03"
        assert hm.get("router_reforma") == "R01"


class TestHashMapOperators:
    """Tests de operadores mágicos."""

    def test_setitem_getitem(self):
        hm = HashMap()
        hm["clave"] = "valor"
        assert hm["clave"] == "valor"

    def test_repr_not_empty(self):
        hm = HashMap()
        hm.put("k", 1)
        r = repr(hm)
        assert "HashMap" in r
        assert "size=1" in r
