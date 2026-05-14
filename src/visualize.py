"""
visualize.py — Visualización de la red ISP con matplotlib.

Dibuja el grafo de la red ISP mostrando:
  - Nodos coloreados por tipo (servidor, router, switch, usuario)
  - Todas las aristas del grafo (gris claro)
  - Aristas del MST (verde, más gruesas)
  - Ruta Dijkstra (rojo, más gruesa)
  - Servidor más cercano (estrella dorada)
  - Nuevo cliente (triángulo cian)
  - Etiquetas de nodos
  - Leyenda completa
"""

from typing import List, Optional, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from src.graph import Graph
from src.models import Edge, Node

# Colores por tipo de nodo
_NODE_COLORS = {
    "server": "#e74c3c",   # Rojo
    "router": "#3498db",   # Azul
    "switch": "#f39c12",   # Naranja
    "user":   "#27ae60",   # Verde
}

# Marcadores por tipo de nodo
_NODE_MARKERS = {
    "server": "s",   # cuadrado
    "router": "o",   # círculo
    "switch": "D",   # diamante
    "user":   "^",   # triángulo arriba
}

_NODE_SIZES = {
    "server": 300,
    "router": 200,
    "switch": 180,
    "user":   160,
}


def plot_network(
    graph: Graph,
    mst_edges: Optional[List[Edge]] = None,
    dijkstra_path: Optional[List[str]] = None,
    nearest_server: Optional[Node] = None,
    new_client: Optional[Tuple[float, float]] = None,
    title: str = "NetOptimizer — Red ISP CDMX",
    save_path: Optional[str] = None,
    show: bool = True,
) -> None:
    """
    Genera la visualización completa de la red ISP.

    Args:
        graph:          Grafo de la red ISP.
        mst_edges:      Aristas del MST (Prim). Si None, no se dibujan.
        dijkstra_path:  Lista de node_ids del camino óptimo (Dijkstra).
        nearest_server: Nodo servidor más cercano al nuevo cliente (KD-tree).
        new_client:     Tupla (lat, lon) del nuevo cliente.
        title:          Título del gráfico.
        save_path:      Si se provee, guarda la imagen en esa ruta.
        show:           Si True, llama a plt.show().
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#16213e")

    all_nodes = graph.get_all_nodes()
    all_edges = graph.get_all_edges()

    # Conjuntos para identificación rápida
    mst_edge_set = set()
    if mst_edges:
        for e in mst_edges:
            key = tuple(sorted([e.source, e.target]))
            mst_edge_set.add(key)

    dijkstra_edge_set = set()
    if dijkstra_path and len(dijkstra_path) > 1:
        for i in range(len(dijkstra_path) - 1):
            key = tuple(sorted([dijkstra_path[i], dijkstra_path[i + 1]]))
            dijkstra_edge_set.add(key)

    # ── 1. Dibujar aristas base (todas) ──────────────────────────────────────
    for (src_id, tgt_id, latency, cost) in all_edges:
        try:
            src = graph.get_node(src_id)
            tgt = graph.get_node(tgt_id)
        except KeyError:
            continue
        # Usar longitud como X, latitud como Y (convención geográfica)
        ax.plot(
            [src.lon, tgt.lon],
            [src.lat, tgt.lat],
            color="#444466",
            linewidth=0.8,
            alpha=0.5,
            zorder=1,
        )

    # ── 2. Dibujar MST (verde) ────────────────────────────────────────────────
    if mst_edges:
        for e in mst_edges:
            try:
                src = graph.get_node(e.source)
                tgt = graph.get_node(e.target)
            except KeyError:
                continue
            ax.plot(
                [src.lon, tgt.lon],
                [src.lat, tgt.lat],
                color="#2ecc71",
                linewidth=2.5,
                alpha=0.85,
                zorder=2,
                solid_capstyle="round",
            )

    # ── 3. Dibujar ruta Dijkstra (rojo) ──────────────────────────────────────
    if dijkstra_path and len(dijkstra_path) > 1:
        for i in range(len(dijkstra_path) - 1):
            try:
                src = graph.get_node(dijkstra_path[i])
                tgt = graph.get_node(dijkstra_path[i + 1])
            except KeyError:
                continue
            ax.plot(
                [src.lon, tgt.lon],
                [src.lat, tgt.lat],
                color="#e74c3c",
                linewidth=3.5,
                alpha=0.95,
                zorder=3,
                solid_capstyle="round",
            )
            # Flecha de dirección
            mid_lon = (src.lon + tgt.lon) / 2
            mid_lat = (src.lat + tgt.lat) / 2
            ax.annotate(
                "",
                xy=(tgt.lon, tgt.lat),
                xytext=(mid_lon, mid_lat),
                arrowprops=dict(
                    arrowstyle="->",
                    color="#ff6b6b",
                    lw=1.5,
                ),
                zorder=4,
            )

    # ── 4. Dibujar nodos ─────────────────────────────────────────────────────
    for node in all_nodes:
        color = _NODE_COLORS.get(node.node_type, "#ffffff")
        marker = _NODE_MARKERS.get(node.node_type, "o")
        size = _NODE_SIZES.get(node.node_type, 150)

        # Resaltar servidor más cercano
        if nearest_server and node.node_id == nearest_server.node_id:
            ax.scatter(
                node.lon, node.lat,
                c="#ffd700",
                s=500,
                marker="*",
                zorder=6,
                edgecolors="#ffffff",
                linewidths=1.5,
            )
        else:
            ax.scatter(
                node.lon, node.lat,
                c=color,
                s=size,
                marker=marker,
                zorder=5,
                edgecolors="#ffffff",
                linewidths=0.8,
                alpha=0.95,
            )

        # Etiqueta del nodo (nombre corto)
        short_name = node.name.replace("Servidor-", "SRV\n").replace(
            "Router-", "R-"
        ).replace("Switch-", "SW-").replace("Usuario-", "U-")
        ax.annotate(
            short_name,
            (node.lon, node.lat),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=7,
            color="#e0e0e0",
            zorder=7,
            fontfamily="monospace",
        )

    # ── 5. Nuevo cliente ──────────────────────────────────────────────────────
    if new_client:
        lat_c, lon_c = new_client
        ax.scatter(
            lon_c, lat_c,
            c="#00bcd4",
            s=350,
            marker="P",  # Plus/Cruz
            zorder=8,
            edgecolors="#ffffff",
            linewidths=2,
        )
        ax.annotate(
            "Nuevo\nCliente",
            (lon_c, lat_c),
            textcoords="offset points",
            xytext=(8, -16),
            fontsize=8,
            color="#00bcd4",
            fontweight="bold",
            zorder=9,
        )

    # ── 6. Leyenda ────────────────────────────────────────────────────────────
    legend_elements = [
        mpatches.Patch(color=_NODE_COLORS["server"],  label="Servidor"),
        mpatches.Patch(color=_NODE_COLORS["router"],  label="Router"),
        mpatches.Patch(color=_NODE_COLORS["switch"],  label="Switch"),
        mpatches.Patch(color=_NODE_COLORS["user"],    label="Usuario"),
        mpatches.Patch(color="#ffd700",               label="Servidor más cercano (KD-tree)"),
        mpatches.Patch(color="#00bcd4",               label="Nuevo Cliente"),
        mpatches.Patch(color="#2ecc71",               label="MST — Red de fibra (Prim)"),
        mpatches.Patch(color="#e74c3c",               label="Ruta óptima (Dijkstra)"),
    ]
    legend = ax.legend(
        handles=legend_elements,
        loc="lower left",
        fontsize=8,
        facecolor="#1a1a2e",
        edgecolor="#555577",
        labelcolor="#e0e0e0",
        framealpha=0.9,
    )

    # ── 7. Estilo del gráfico ─────────────────────────────────────────────────
    ax.set_title(title, color="#e0e0e0", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Longitud", color="#aaaacc", fontsize=9)
    ax.set_ylabel("Latitud", color="#aaaacc", fontsize=9)
    ax.tick_params(colors="#aaaacc", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333355")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"[visualize] Imagen guardada en: {save_path}")

    if show:
        plt.show()

    plt.close(fig)
