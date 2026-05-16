"""
data_loader.py — Carga de datos CSV hacia objetos del grafo ISP.

Lee nodes.csv y edges.csv y construye un objeto Graph listo para usar.
También puede generar datos sintéticos si los archivos no existen.
"""

import os
from typing import Optional

import pandas as pd

from src.graph import Graph
from src.models import Edge, Node

# Rutas por defecto de los archivos de datos
_DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_NODES_FILE = os.path.join(_DEFAULT_DATA_DIR, "nodes.csv")
_EDGES_FILE = os.path.join(_DEFAULT_DATA_DIR, "edges.csv")


def load_graph(
    nodes_path: str = _NODES_FILE,
    edges_path: str = _EDGES_FILE,
    verbose: bool = False,
) -> Graph:
    """
    Carga el grafo ISP desde archivos CSV.

    Lee nodes.csv y edges.csv, valida los campos requeridos
    y construye un objeto Graph con todos los nodos y aristas.

    Parámetros:
        nodes_path: Ruta al archivo CSV de nodos.
        edges_path: Ruta al archivo CSV de aristas.
        verbose:    Si True, imprime resumen de carga.

    Retorna:
        Objeto Graph listo para usar.

    Raises:
        FileNotFoundError: Si alguno de los archivos no existe.
        ValueError:        Si faltan columnas requeridas en los CSV.
    """
    # ── Cargar nodos ─────────────────────────────────────────────────────────
    if not os.path.exists(nodes_path):
        raise FileNotFoundError(f"Archivo de nodos no encontrado: {nodes_path}")

    nodes_df = pd.read_csv(nodes_path)
    _validate_columns(
        nodes_df,
        required=["node_id", "name", "node_type", "lat", "lon"],
        file_name=nodes_path,
    )

    # ── Cargar aristas ────────────────────────────────────────────────────────
    if not os.path.exists(edges_path):
        raise FileNotFoundError(f"Archivo de aristas no encontrado: {edges_path}")

    edges_df = pd.read_csv(edges_path)
    _validate_columns(
        edges_df,
        required=["source", "target", "latency_ms", "cost_usd", "bandwidth_gbps"],
        file_name=edges_path,
    )

    # ── Construir el grafo ────────────────────────────────────────────────────
    graph = Graph()

    # Insertar nodos
    skipped_nodes = 0
    for _, row in nodes_df.iterrows():
        try:
            node = Node(
                node_id=str(row["node_id"]).strip(),
                name=str(row["name"]).strip(),
                node_type=str(row["node_type"]).strip(),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
            )
            graph.add_node(node)
        except (ValueError, KeyError) as e:
            print(f"[data_loader] Advertencia: nodo inválido en fila {_}: {e}")
            skipped_nodes += 1

    # Insertar aristas
    skipped_edges = 0
    for _, row in edges_df.iterrows():
        try:
            edge = Edge(
                source=str(row["source"]).strip(),
                target=str(row["target"]).strip(),
                latency_ms=float(row["latency_ms"]),
                cost_usd=float(row["cost_usd"]),
                bandwidth_gbps=float(row["bandwidth_gbps"]),
            )
            graph.add_edge(edge)
        except (ValueError, KeyError) as e:
            print(f"[data_loader] Advertencia: arista inválida en fila {_}: {e}")
            skipped_edges += 1

    if verbose:
        print(f"[data_loader] Nodos cargados:  {graph.num_nodes} "
              f"(omitidos: {skipped_nodes})")
        print(f"[data_loader] Aristas cargadas: {graph.num_edges} "
              f"(omitidas: {skipped_edges})")
        print(graph.summary())

    return graph


def _validate_columns(df: pd.DataFrame, required: list, file_name: str) -> None:
    """
    Verifica que el DataFrame contenga todas las columnas requeridas.

    Parámetros:
        df:        DataFrame a validar.
        required:  Lista de nombres de columnas requeridas.
        file_name: Nombre del archivo (para mensajes de error).

    Raises:
        ValueError: Si faltan columnas requeridas.
    """
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Columnas faltantes en '{file_name}': {missing}\n"
            f"Columnas encontradas: {list(df.columns)}"
        )


if __name__ == "__main__":
    # Prueba rápida de carga
    graph = load_graph(verbose=True)
    print(f"\nGrafo cargado: {graph}")
    servers = graph.get_nodes_by_type("server")
    print(f"Servidores: {[s.name for s in servers]}")
