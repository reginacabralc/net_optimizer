"""
models.py — Estructuras de datos base para NetOptimizer.

Define Node y Edge como dataclasses inmutables.
"""

from dataclasses import dataclass
from typing import Optional


# Tipos de nodo válidos en la red ISP
NODE_TYPES = {"server", "router", "switch", "user"}


@dataclass(frozen=True)
class Node:
    """
    Representa un nodo en la red ISP.

    Attributes:
        node_id:   Identificador único (ej: '1', '10').
        name:      Nombre legible (ej: 'Datacenter Norte').
        node_type: Tipo de nodo: 'server' | 'router' | 'switch' | 'user'.
        lat:       Latitud GPS (grados decimales).
        lon:       Longitud GPS (grados decimales).
    """

    node_id: str
    name: str
    node_type: str
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if self.node_type not in NODE_TYPES:
            raise ValueError(
                f"node_type '{self.node_type}' inválido. "
                f"Debe ser uno de: {NODE_TYPES}"
            )
        if not (-90 <= self.lat <= 90):
            raise ValueError(f"Latitud inválida: {self.lat}")
        if not (-180 <= self.lon <= 180):
            raise ValueError(f"Longitud inválida: {self.lon}")

    def __repr__(self) -> str:
        return f"Node({self.node_id}, {self.name}, {self.node_type})"


@dataclass(frozen=True)
class Edge:
    """
    Representa una conexión (arista) entre dos nodos en la red ISP.

    Attributes:
        source:      node_id del nodo origen.
        target:      node_id del nodo destino.
        latency_ms:     Latencia de la conexión en milisegundos (≥ 0).
        cost_usd:       Costo de instalación del cable en USD (≥ 0).
        bandwidth_gbps: Capacidad del enlace en gigabits por segundo (≥ 0).
    """

    source: str
    target: str
    latency_ms: float
    cost_usd: float
    bandwidth_gbps: float = 10.0

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError(f"latency_ms no puede ser negativa: {self.latency_ms}")
        if self.cost_usd < 0:
            raise ValueError(f"cost_usd no puede ser negativo: {self.cost_usd}")
        if self.bandwidth_gbps < 0:
            raise ValueError(
                f"bandwidth_gbps no puede ser negativo: {self.bandwidth_gbps}"
            )

    def __repr__(self) -> str:
        return (
            f"Edge({self.source}→{self.target}, "
            f"{self.latency_ms}ms, ${self.cost_usd}, "
            f"{self.bandwidth_gbps}Gbps)"
        )
