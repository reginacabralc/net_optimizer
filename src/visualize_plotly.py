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


def _base_edges_xy(graph: Graph):
    """Returns (x_list, y_list) for all edges as a single Scatter-compatible sequence."""
    xs, ys = [], []
    for (src_id, tgt_id, _, _) in graph.get_all_edges():
        try:
            src = graph.get_node(src_id)
            tgt = graph.get_node(tgt_id)
            xs += [src.lon, tgt.lon, None]
            ys += [src.lat, tgt.lat, None]
        except KeyError:
            pass
    return xs, ys


def _animation_layout(title: str, n_frames: int, speed_ms: int) -> go.Layout:
    """Shared Plotly layout for timelapse figures."""
    return go.Layout(
        title=title,
        paper_bgcolor="#faf8f4",
        plot_bgcolor="#f5f0e8",
        font=dict(color="#2c2416", family="monospace"),
        height=540,
        margin=dict(l=40, r=20, t=90, b=40),
        xaxis=dict(title="Longitud", gridcolor="#e8e0d0", zerolinecolor="#ccc0a8"),
        yaxis=dict(
            title="Latitud", gridcolor="#e8e0d0", zerolinecolor="#ccc0a8",
            scaleanchor="x", scaleratio=1,
        ),
        updatemenus=[dict(
            type="buttons",
            direction="left",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[None, {
                        "frame": {"duration": speed_ms, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 0},
                    }],
                ),
                dict(
                    label="⏸ Pausa",
                    method="animate",
                    args=[[None], {
                        "frame": {"duration": 0},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    }],
                ),
            ],
            bgcolor="#ffffff",
            font=dict(color="#2c2416"),
            x=0.01, y=1.18,
        )],
        sliders=[dict(
            steps=[
                dict(
                    method="animate",
                    args=[[str(i)], {
                        "mode": "immediate",
                        "frame": {"duration": speed_ms, "redraw": True},
                        "transition": {"duration": 0},
                    }],
                    label=str(i + 1),
                )
                for i in range(n_frames)
            ],
            currentvalue=dict(prefix="Paso: ", font=dict(size=12)),
            bgcolor="#ffffff",
            font=dict(color="#2c2416"),
            pad=dict(t=60),
        )],
    )


def build_dijkstra_map_timelapse(
    steps: List[dict],
    graph: Graph,
    speed_ms: int = 600,
) -> go.Figure:
    """
    Mapa animado que muestra cómo Dijkstra se expande como una colonia.

    Cada frame muestra:
      - Aristas base (gris tenue, estáticas)
      - Árbol de caminos mínimos creciendo (cian)
      - Nodos asentados (cian, crecen)
      - Nodo actual siendo procesado (estrella dorada)
      - Nodos no visitados (opacidad baja)
    """
    if not steps:
        return go.Figure()

    all_nodes = list(graph.get_all_nodes())
    base_x, base_y = _base_edges_xy(graph)

    def _traces(step: dict) -> list:
        visited_set = set(step["visited"])
        current = step["current"]
        prev = step["prev"]

        # Shortest-path tree edges (settled prev pointers)
        tree_x, tree_y = [], []
        for nid in step["visited"]:
            parent = prev.get(nid)
            if parent is not None:
                try:
                    n = graph.get_node(nid)
                    p = graph.get_node(parent)
                    tree_x += [p.lon, n.lon, None]
                    tree_y += [p.lat, n.lat, None]
                except KeyError:
                    pass

        unvisited = [n for n in all_nodes if n.node_id not in visited_set]
        settled = [n for n in all_nodes if n.node_id in visited_set and n.node_id != current]
        try:
            curr_node = graph.get_node(current)
            curr_nodes = [curr_node]
        except KeyError:
            curr_nodes = []

        return [
            # 0 — base edges
            go.Scatter(
                x=base_x, y=base_y, mode="lines",
                line=dict(color="rgba(58,58,92,0.22)", width=0.9),
                hoverinfo="skip", showlegend=False,
            ),
            # 1 — shortest-path tree (cian)
            go.Scatter(
                x=tree_x, y=tree_y, mode="lines",
                line=dict(color="#00bcd4", width=2.8),
                showlegend=False, hoverinfo="skip",
            ),
            # 2 — unvisited nodes (dimmed)
            go.Scatter(
                x=[n.lon for n in unvisited],
                y=[n.lat for n in unvisited],
                mode="markers",
                marker=dict(size=9, color="rgba(58,58,92,0.28)"),
                hoverinfo="skip", showlegend=False,
            ),
            # 3 — settled nodes (cian)
            go.Scatter(
                x=[n.lon for n in settled],
                y=[n.lat for n in settled],
                mode="markers+text",
                marker=dict(
                    size=[_SIZES[n.node_type] for n in settled] if settled else 9,
                    color="#00bcd4",
                    symbol=[_SYMBOLS[n.node_type] for n in settled] if settled else "circle",
                    line=dict(color="#ffffff", width=1.5),
                ),
                text=[n.name.split("-", 1)[-1] for n in settled],
                textposition="top center",
                textfont=dict(size=8, color="#00bcd4"),
                showlegend=False,
            ),
            # 4 — current node (gold star)
            go.Scatter(
                x=[n.lon for n in curr_nodes],
                y=[n.lat for n in curr_nodes],
                mode="markers+text",
                marker=dict(
                    size=24,
                    color="#ffd700",
                    symbol=[_SYMBOLS[n.node_type] for n in curr_nodes] if curr_nodes else "star",
                    line=dict(color="#ffffff", width=2),
                ),
                text=[n.name.split("-", 1)[-1] for n in curr_nodes],
                textposition="top center",
                textfont=dict(size=10, color="#ffd700", family="Arial Black"),
                showlegend=False,
            ),
        ]

    frames = []
    for i, step in enumerate(steps):
        try:
            node_name = graph.get_node(step["current"]).name.split("-", 1)[-1]
        except KeyError:
            node_name = step["current"]
        frames.append(go.Frame(
            data=_traces(step),
            name=str(i),
            layout=go.Layout(
                title_text=(
                    f"Dijkstra — Paso {i + 1}/{len(steps)}: "
                    f"asentando '{node_name}'"
                )
            ),
        ))

    layout = _animation_layout(
        "Dijkstra — Expansión de la colonia sobre la red",
        len(frames),
        speed_ms,
    )
    return go.Figure(data=_traces(steps[0]), frames=frames, layout=layout)


def build_prim_map_timelapse(
    steps: List[dict],
    graph: Graph,
    speed_ms: int = 600,
) -> go.Figure:
    """
    Mapa animado que muestra cómo Prim construye el MST como una colonia.

    Cada frame muestra:
      - Aristas base (gris tenue, estáticas)
      - MST acumulado (verde)
      - Arista recién añadida (dorada)
      - Nodo recién añadido (estrella dorada)
      - Nodos ya en MST (verde, crecen)
      - Nodos fuera del MST (opacidad baja)
    """
    if not steps:
        return go.Figure()

    all_nodes = list(graph.get_all_nodes())
    base_x, base_y = _base_edges_xy(graph)

    def _traces(step: dict) -> list:
        in_mst = step["in_mst"]
        mst_edges_so_far = step["mst_edges"]
        current_edge = step.get("current_edge")
        new_node_id = current_edge.target if current_edge else None

        # MST edges already settled (green), excluding the current one
        mst_x, mst_y = [], []
        for e in mst_edges_so_far:
            if current_edge and e.source == current_edge.source and e.target == current_edge.target:
                continue
            try:
                src = graph.get_node(e.source)
                tgt = graph.get_node(e.target)
                mst_x += [src.lon, tgt.lon, None]
                mst_y += [src.lat, tgt.lat, None]
            except KeyError:
                pass

        # Current edge being added (gold)
        cur_ex, cur_ey = [], []
        if current_edge:
            try:
                src = graph.get_node(current_edge.source)
                tgt = graph.get_node(current_edge.target)
                cur_ex = [src.lon, tgt.lon]
                cur_ey = [src.lat, tgt.lat]
            except KeyError:
                pass

        not_in_mst = [n for n in all_nodes if n.node_id not in in_mst]
        settled_mst = [n for n in all_nodes if n.node_id in in_mst and n.node_id != new_node_id]
        new_nodes = []
        if new_node_id:
            try:
                new_nodes = [graph.get_node(new_node_id)]
            except KeyError:
                pass

        return [
            # 0 — base edges
            go.Scatter(
                x=base_x, y=base_y, mode="lines",
                line=dict(color="rgba(58,58,92,0.22)", width=0.9),
                hoverinfo="skip", showlegend=False,
            ),
            # 1 — settled MST edges (green)
            go.Scatter(
                x=mst_x, y=mst_y, mode="lines",
                line=dict(color="#2ecc71", width=3),
                showlegend=False, hoverinfo="skip",
            ),
            # 2 — current edge being added (gold)
            go.Scatter(
                x=cur_ex, y=cur_ey, mode="lines",
                line=dict(color="#ffd700", width=5),
                showlegend=False, hoverinfo="skip",
            ),
            # 3 — nodes outside MST (dimmed)
            go.Scatter(
                x=[n.lon for n in not_in_mst],
                y=[n.lat for n in not_in_mst],
                mode="markers",
                marker=dict(size=9, color="rgba(58,58,92,0.28)"),
                hoverinfo="skip", showlegend=False,
            ),
            # 4 — nodes already in MST (green)
            go.Scatter(
                x=[n.lon for n in settled_mst],
                y=[n.lat for n in settled_mst],
                mode="markers+text",
                marker=dict(
                    size=[_SIZES[n.node_type] for n in settled_mst] if settled_mst else 9,
                    color="#2ecc71",
                    symbol=[_SYMBOLS[n.node_type] for n in settled_mst] if settled_mst else "circle",
                    line=dict(color="#ffffff", width=1.5),
                ),
                text=[n.name.split("-", 1)[-1] for n in settled_mst],
                textposition="top center",
                textfont=dict(size=8, color="#2ecc71"),
                showlegend=False,
            ),
            # 5 — newly added node (gold burst)
            go.Scatter(
                x=[n.lon for n in new_nodes],
                y=[n.lat for n in new_nodes],
                mode="markers+text",
                marker=dict(
                    size=24,
                    color="#ffd700",
                    symbol=[_SYMBOLS[n.node_type] for n in new_nodes] if new_nodes else "star",
                    line=dict(color="#ffffff", width=2),
                ),
                text=[n.name.split("-", 1)[-1] for n in new_nodes],
                textposition="top center",
                textfont=dict(size=10, color="#ffd700", family="Arial Black"),
                showlegend=False,
            ),
        ]

    frames = []
    for i, step in enumerate(steps):
        ce = step.get("current_edge")
        if ce:
            try:
                src_n = graph.get_node(ce.source).name.split("-", 1)[-1]
                tgt_n = graph.get_node(ce.target).name.split("-", 1)[-1]
                title = (
                    f"Prim — Paso {i + 1}/{len(steps)}: "
                    f"conectando '{src_n}' → '{tgt_n}'  "
                    f"(${ce.cost_usd:,.0f} USD · {ce.latency_ms} ms)"
                )
            except KeyError:
                title = f"Prim — Paso {i + 1}/{len(steps)}"
        else:
            try:
                start_name = graph.get_node(next(iter(step["in_mst"]))).name.split("-", 1)[-1]
                title = f"Prim — Inicio desde '{start_name}'"
            except (StopIteration, KeyError):
                title = "Prim — Inicio"

        frames.append(go.Frame(
            data=_traces(step),
            name=str(i),
            layout=go.Layout(title_text=title),
        ))

    layout = _animation_layout(
        "Prim MST — Crecimiento del árbol de fibra",
        len(frames),
        speed_ms,
    )
    return go.Figure(data=_traces(steps[0]), frames=frames, layout=layout)


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
