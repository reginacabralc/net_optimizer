"""
visualize_plotly.py — Gráfico interactivo de red ISP con Plotly.

Genera un plotly.graph_objects.Figure con:
  - Nodos coloreados por tipo (hover con info detallada)
  - Aristas base (gris)
  - MST resaltado (verde)
  - Ruta Dijkstra resaltada (rojo con flechas)
  - Servidor más cercano (estrella dorada)
  - Nuevo cliente (cruz cian)
"""

from typing import List, Optional, Tuple

import plotly.graph_objects as go

from src.graph import Graph
from src.models import Edge, Node

# Paleta de colores por tipo de nodo
_COLORS = {
    "server": "#e74c3c",
    "router": "#3498db",
    "switch": "#f39c12",
    "user":   "#2ecc71",
}

_SYMBOLS = {
    "server": "square",
    "router": "circle",
    "switch": "diamond",
    "user":   "triangle-up",
}

_SIZES = {
    "server": 18,
    "router": 14,
    "switch": 13,
    "user":   13,
}

_LABELS_ES = {
    "server": "Servidor",
    "router": "Router",
    "switch": "Switch",
    "user":   "Usuario",
}


def build_network_figure(
    graph: Graph,
    mst_edges: Optional[List[Edge]] = None,
    dijkstra_path: Optional[List[str]] = None,
    nearest_server: Optional[Node] = None,
    new_client: Optional[Tuple[float, float]] = None,
    dijkstra_steps: Optional[List[dict]] = None,
) -> go.Figure:
    """
    Construye la figura Plotly interactiva de la red ISP.

    Args:
        graph:           Grafo de la red ISP.
        mst_edges:       Aristas del MST (Prim).
        dijkstra_path:   Lista de node_ids de la ruta óptima.
        nearest_server:  Nodo servidor más cercano (KD-tree).
        new_client:      (lat, lon) del nuevo cliente.
        dijkstra_steps:  Pasos intermedios de Dijkstra para animación.

    Returns:
        Figura Plotly lista para renderizar en Streamlit.
    """
    fig = go.Figure()

    mst_set = set()
    if mst_edges:
        for e in mst_edges:
            mst_set.add(tuple(sorted([e.source, e.target])))

    dijkstra_set = set()
    if dijkstra_path and len(dijkstra_path) > 1:
        for i in range(len(dijkstra_path) - 1):
            dijkstra_set.add(tuple(sorted([dijkstra_path[i], dijkstra_path[i+1]])))

    all_edges = graph.get_all_edges()

    # ── Aristas base ──────────────────────────────────────────────────────────
    for (src_id, tgt_id, latency, cost) in all_edges:
        key = tuple(sorted([src_id, tgt_id]))
        if key in dijkstra_set or key in mst_set:
            continue  # se dibujan después con estilo propio
        try:
            src = graph.get_node(src_id)
            tgt = graph.get_node(tgt_id)
        except KeyError:
            continue
        fig.add_trace(go.Scatter(
            x=[src.lon, tgt.lon, None],
            y=[src.lat, tgt.lat, None],
            mode="lines",
            line=dict(color="#3a3a5c", width=1.2),
            hoverinfo="skip",
            showlegend=False,
        ))

    # ── Aristas MST (verde) ───────────────────────────────────────────────────
    if mst_edges:
        mst_x, mst_y = [], []
        for e in mst_edges:
            try:
                src = graph.get_node(e.source)
                tgt = graph.get_node(e.target)
            except KeyError:
                continue
            mst_x += [src.lon, tgt.lon, None]
            mst_y += [src.lat, tgt.lat, None]
        fig.add_trace(go.Scatter(
            x=mst_x, y=mst_y,
            mode="lines",
            name="MST — Prim (fibra mínima)",
            line=dict(color="#2ecc71", width=3),
            opacity=0.85,
        ))

    # ── Ruta Dijkstra (rojo) ──────────────────────────────────────────────────
    if dijkstra_path and len(dijkstra_path) > 1:
        dij_x, dij_y = [], []
        for nid in dijkstra_path:
            try:
                n = graph.get_node(nid)
                dij_x.append(n.lon)
                dij_y.append(n.lat)
            except KeyError:
                continue
        fig.add_trace(go.Scatter(
            x=dij_x, y=dij_y,
            mode="lines+markers",
            name="Ruta óptima — Dijkstra",
            line=dict(color="#e74c3c", width=4),
            marker=dict(size=6, color="#ff6b6b",
                        symbol="arrow", angleref="previous"),
            opacity=0.95,
        ))

    # ── Nodos por tipo ────────────────────────────────────────────────────────
    for ntype in ["server", "router", "switch", "user"]:
        nodes_of_type = [
            n for n in graph.get_all_nodes()
            if n.node_type == ntype
            and not (nearest_server and n.node_id == nearest_server.node_id)
        ]
        if not nodes_of_type:
            continue

        hover = [
            f"<b>{n.name}</b><br>"
            f"Tipo: {_LABELS_ES[n.node_type]}<br>"
            f"ID: {n.node_id}<br>"
            f"Lat: {n.lat:.4f}<br>"
            f"Lon: {n.lon:.4f}"
            for n in nodes_of_type
        ]

        fig.add_trace(go.Scatter(
            x=[n.lon for n in nodes_of_type],
            y=[n.lat for n in nodes_of_type],
            mode="markers+text",
            name=_LABELS_ES[ntype],
            marker=dict(
                size=_SIZES[ntype],
                color=_COLORS[ntype],
                symbol=_SYMBOLS[ntype],
                line=dict(color="#ffffff", width=1.5),
            ),
            text=[n.name.split("-", 1)[-1] for n in nodes_of_type],
            textposition="top center",
            textfont=dict(size=9, color="#2c2416"),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover,
        ))

    # ── Servidor más cercano (estrella dorada) ────────────────────────────────
    if nearest_server:
        fig.add_trace(go.Scatter(
            x=[nearest_server.lon],
            y=[nearest_server.lat],
            mode="markers+text",
            name=f"Servidor más cercano ({nearest_server.name})",
            marker=dict(
                size=28,
                color="#ffd700",
                symbol="star",
                line=dict(color="#ffffff", width=2),
            ),
            text=[nearest_server.name.split("-", 1)[-1]],
            textposition="top center",
            textfont=dict(size=10, color="#ffd700", family="Arial Black"),
            hovertemplate=(
                f"<b>⭐ SERVIDOR MÁS CERCANO</b><br>"
                f"{nearest_server.name}<br>"
                f"ID: {nearest_server.node_id}<br>"
                f"Lat: {nearest_server.lat}<br>"
                f"Lon: {nearest_server.lon}"
                "<extra></extra>"
            ),
        ))

    # ── Nuevo cliente ─────────────────────────────────────────────────────────
    if new_client:
        lat_c, lon_c = new_client
        fig.add_trace(go.Scatter(
            x=[lon_c], y=[lat_c],
            mode="markers+text",
            name="Nuevo Cliente",
            marker=dict(
                size=20,
                color="#00bcd4",
                symbol="cross",
                line=dict(color="#ffffff", width=2),
            ),
            text=["Nuevo Cliente"],
            textposition="bottom center",
            textfont=dict(size=10, color="#00bcd4", family="Arial Black"),
            hovertemplate=(
                f"<b>📍 NUEVO CLIENTE</b><br>"
                f"Lat: {lat_c:.4f}<br>"
                f"Lon: {lon_c:.4f}"
                "<extra></extra>"
            ),
        ))

    # ── Layout ────────────────────────────────────────────────────────────────
    fig.update_layout(
        paper_bgcolor="#faf8f4",
        plot_bgcolor="#f5f0e8",
        font=dict(color="#2c2416", family="monospace"),
        legend=dict(
            bgcolor="#ffffff",
            bordercolor="#ccc5b0",
            borderwidth=1,
            font=dict(size=11),
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
        ),
        xaxis=dict(
            title="Longitud",
            gridcolor="#e8e0d0",
            zerolinecolor="#ccc0a8",
            tickfont=dict(size=9, color="#5a4a38"),
        ),
        yaxis=dict(
            title="Latitud",
            gridcolor="#e8e0d0",
            zerolinecolor="#ccc0a8",
            tickfont=dict(size=9, color="#5a4a38"),
            scaleanchor="x",
            scaleratio=1,
        ),
        hovermode="closest",
        margin=dict(l=40, r=20, t=60, b=40),
        height=560,
    )

    return fig


def build_complexity_chart() -> go.Figure:
    """
    Gráfica comparativa de complejidad: HashMap O(1) vs búsqueda lineal O(n).
    Muestra tiempo de búsqueda real en microsegundos para distintos n.
    """
    import time
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.hash_map import HashMap

    ns = [10, 50, 100, 500, 1000, 5000, 10000]
    hashmap_times = []
    linear_times = []
    REPS = 500

    for n in ns:
        # Construir HashMap
        hm = HashMap()
        items = [f"nodo_{i:06d}" for i in range(n)]
        for key in items:
            hm.put(key, key)
        target = items[n // 2]

        # Medir HashMap
        t0 = time.perf_counter()
        for _ in range(REPS):
            hm.get(target)
        hashmap_times.append((time.perf_counter() - t0) / REPS * 1e6)

        # Medir búsqueda lineal (list)
        lst = list(items)
        t0 = time.perf_counter()
        for _ in range(REPS):
            _ = lst.index(target)
        linear_times.append((time.perf_counter() - t0) / REPS * 1e6)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ns, y=hashmap_times,
        mode="lines+markers",
        name="HashMap — O(1) promedio",
        line=dict(color="#2ecc71", width=3),
        marker=dict(size=9),
    ))
    fig.add_trace(go.Scatter(
        x=ns, y=linear_times,
        mode="lines+markers",
        name="Búsqueda lineal — O(n)",
        line=dict(color="#e74c3c", width=3),
        marker=dict(size=9),
    ))
    fig.update_layout(
        title="HashMap O(1) vs Búsqueda Lineal O(n) — Tiempo real de búsqueda",
        xaxis_title="Número de elementos (n)",
        yaxis_title="Tiempo por búsqueda (µs)",
        paper_bgcolor="#faf8f4",
        plot_bgcolor="#f5f0e8",
        font=dict(color="#2c2416", family="monospace"),
        legend=dict(bgcolor="#ffffff", bordercolor="#ccc5b0", borderwidth=1),
        hovermode="x unified",
        height=380,
    )
    return fig


def build_dijkstra_steps_chart(
    steps: List[dict],
    graph: Graph,
) -> go.Figure:
    """
    Gráfica de barras animada mostrando cómo Dijkstra actualiza distancias.

    Args:
        steps: Lista de dicts con el estado de dist[] en cada iteración.
        graph: Grafo para obtener nombres de nodos.
    """
    if not steps:
        return go.Figure()

    node_ids = list(steps[0]["dist"].keys())
    node_names = []
    for nid in node_ids:
        try:
            node_names.append(graph.get_node(nid).name.split("-", 1)[-1])
        except KeyError:
            node_names.append(nid)

    frames = []
    for i, step in enumerate(steps):
        vals = [
            step["dist"][nid] if step["dist"][nid] != float("inf") else 0
            for nid in node_ids
        ]
        colors = []
        for nid in node_ids:
            if nid == step.get("current"):
                colors.append("#ffd700")
            elif step["dist"][nid] == float("inf"):
                colors.append("#3a3a5c")
            else:
                colors.append("#3498db")

        frames.append(go.Frame(
            data=[go.Bar(
                x=node_names,
                y=vals,
                marker_color=colors,
                text=[
                    f"{v:.0f}ms" if v > 0 else "∞"
                    for v in vals
                ],
                textposition="outside",
                textfont=dict(size=10, color="#2c2416"),
            )],
            name=str(i),
            layout=go.Layout(
                title_text=f"Dijkstra — Paso {i+1}: procesando '{step.get('current', '')}'"
            )
        ))

    initial_vals = [0 if nid == steps[0].get("source") else 0 for nid in node_ids]

    fig = go.Figure(
        data=[go.Bar(
            x=node_names,
            y=initial_vals,
            marker_color="#3498db",
        )],
        frames=frames,
        layout=go.Layout(
            title="Dijkstra — Evolución de distancias mínimas",
            xaxis_title="Nodo",
            yaxis_title="Distancia acumulada (ms)",
            paper_bgcolor="#faf8f4",
            plot_bgcolor="#f5f0e8",
            font=dict(color="#2c2416", family="monospace"),
            height=380,
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    dict(label="▶ Play",
                         method="animate",
                         args=[None, {"frame": {"duration": 700, "redraw": True},
                                      "fromcurrent": True}]),
                    dict(label="⏸ Pause",
                         method="animate",
                         args=[[None], {"frame": {"duration": 0},
                                        "mode": "immediate"}]),
                ],
                bgcolor="#ffffff",
                font=dict(color="#2c2416"),
                x=0.01, y=1.12,
            )],
            sliders=[dict(
                steps=[
                    dict(method="animate",
                         args=[[str(i)], {"mode": "immediate",
                                          "frame": {"duration": 300, "redraw": True}}],
                         label=str(i+1))
                    for i in range(len(frames))
                ],
                currentvalue=dict(prefix="Paso: "),
                bgcolor="#ffffff",
                font=dict(color="#2c2416"),
            )],
        )
    )
    return fig
