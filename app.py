"""
app.py — Dashboard interactivo de NetOptimizer.

Corre con: streamlit run app.py

Tabs:
  🗺  Red ISP      — mapa interactivo con todos los algoritmos
  ⚡  Dijkstra     — animación paso a paso
  🌿  Prim MST     — tabla de aristas del árbol de expansión mínima
  🔍  KD-tree      — comparación servidor más cercano vs todos
  #️⃣  HashMap      — benchmark O(1) vs O(n) con tiempos reales
  📋  Resumen      — tabla de complejidades y guía de presentación
"""

import sys
import os
import time

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_graph
from src.dijkstra import shortest_path, dijkstra_with_steps
from src.kdtree import KDTree, _haversine_dist
from src.prim import prim_mst
from src.hash_map import HashMap
from src.visualize_plotly import (
    build_network_figure,
    build_complexity_chart,
    build_dijkstra_steps_chart,
)

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="NetOptimizer",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #faf8f4; }
  [data-testid="stSidebar"]          { background: #f0ebe0; border-right: 1px solid #ddd5c0; }
  [data-testid="stSidebar"] * { color: #2c2416 !important; }
  h1, h2, h3, h4 { color: #1a120b; }
  .metric-card {
    background: #ffffff;
    border: 1px solid #ddd5c0;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .metric-card .label { color: #8a7d68; font-size: 12px; margin-bottom: 4px; }
  .metric-card .value { color: #1a120b; font-size: 28px; font-weight: bold; }
  .metric-card .sub   { color: #a09080; font-size: 11px; margin-top: 4px; }
  .section-title {
    color: #7a5c2e;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 16px 0 8px 0;
  }
  .algo-badge {
    display: inline-block;
    background: #f0e8d8;
    border: 1px solid #c8b89a;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 11px;
    color: #6b4f2a;
    margin: 2px;
  }
</style>
""", unsafe_allow_html=True)


# ── Cache de datos ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_graph():
    return load_graph(verbose=False)


@st.cache_resource
def get_kdtree(_graph):
    servers = _graph.get_nodes_by_type("server")
    tree = KDTree()
    tree.build(servers)
    return tree


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌐 NetOptimizer")
    st.markdown("**ISP Network Optimizer**")
    st.markdown("---")

    st.markdown('<div class="section-title">📍 Nuevo Cliente</div>', unsafe_allow_html=True)
    client_lat = st.number_input(
        "Latitud", value=19.4326, format="%.4f", step=0.01,
        min_value=19.0, max_value=19.8,
    )
    client_lon = st.number_input(
        "Longitud", value=-99.1332, format="%.4f", step=0.01,
        min_value=-99.6, max_value=-98.8,
    )

    st.markdown('<div class="section-title">🎛️ Opciones</div>', unsafe_allow_html=True)
    show_mst = st.checkbox("Mostrar MST (Prim)", value=True)
    show_dijkstra = st.checkbox("Mostrar ruta Dijkstra", value=True)
    show_kdtree = st.checkbox("Mostrar servidor más cercano (KD-tree)", value=True)

    st.markdown('<div class="section-title">⚡ Origen Dijkstra</div>', unsafe_allow_html=True)
    graph = get_graph()
    all_nodes = sorted(graph.get_all_nodes(), key=lambda n: n.name)
    node_options = {n.name: n.node_id for n in all_nodes}
    source_name = st.selectbox(
        "Nodo origen",
        options=list(node_options.keys()),
        index=0,
    )
    source_id = node_options[source_name]

    st.markdown("---")
    st.markdown(
        '<span class="algo-badge">Dijkstra</span>'
        '<span class="algo-badge">Prim</span>'
        '<span class="algo-badge">KD-tree</span>'
        '<span class="algo-badge">HashMap</span>',
        unsafe_allow_html=True,
    )
    st.caption("Variante 4 · Estructuras de Datos")


# ── Computar resultados ────────────────────────────────────────────────────────
graph = get_graph()
kd_tree = get_kdtree(graph)

nearest, dist_km = kd_tree.nearest_neighbor(client_lat, client_lon)
target_id = nearest.node_id if nearest else graph.get_nodes_by_type("server")[0].node_id

latency, dij_path = shortest_path(graph, source_id, target_id)
first_server = graph.get_nodes_by_type("server")[0].node_id
mst_edges, mst_cost = prim_mst(graph, first_server)

dij_path_names = " → ".join(
    graph.get_node(n).name.split("-", 1)[-1] for n in dij_path
) if dij_path else "Sin ruta"


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 🌐 NetOptimizer — ISP Network Dashboard")
st.markdown(
    f"Red de **{graph.num_nodes} nodos** y **{graph.num_edges} aristas** · "
    f"Ciudad de México"
)

# ── Métricas rápidas ───────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
      <div class="label">🔍 KD-tree — Distancia</div>
      <div class="value">{dist_km:.2f} km</div>
      <div class="sub">Servidor: {nearest.name.split('-',1)[-1] if nearest else '—'}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    latency_display = f"{latency:.0f} ms" if latency != float("inf") else "∞"
    st.markdown(f"""
    <div class="metric-card">
      <div class="label">⚡ Dijkstra — Latencia</div>
      <div class="value">{latency_display}</div>
      <div class="sub">{len(dij_path)-1 if dij_path else 0} saltos</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
      <div class="label">🌿 Prim — Costo MST</div>
      <div class="value">${mst_cost:,.0f}</div>
      <div class="sub">{len(mst_edges)} aristas de fibra</div>
    </div>""", unsafe_allow_html=True)

with c4:
    hm = graph.node_index
    st.markdown(f"""
    <div class="metric-card">
      <div class="label">#️⃣ HashMap — Load Factor</div>
      <div class="value">{hm._load_factor():.2f}</div>
      <div class="sub">{len(hm)} entradas · {hm._capacity} buckets</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗺️  Red ISP",
    "⚡  Dijkstra paso a paso",
    "🌿  Prim MST",
    "🔍  KD-tree",
    "#️⃣  HashMap",
    "📋  Complejidad",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Red ISP
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    fig = build_network_figure(
        graph=graph,
        mst_edges=mst_edges if show_mst else None,
        dijkstra_path=dij_path if show_dijkstra else None,
        nearest_server=nearest if show_kdtree else None,
        new_client=(client_lat, client_lon),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Info de la ruta
    if dij_path and show_dijkstra:
        st.info(
            f"**Ruta Dijkstra:** {dij_path_names}  |  "
            f"**Latencia total:** {latency:.0f} ms  |  "
            f"**Saltos:** {len(dij_path)-1}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Dijkstra paso a paso
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ⚡ Dijkstra — Animación de distancias mínimas")
    st.markdown(
        "Cada barra muestra la **distancia mínima acumulada** desde el nodo origen. "
        "La barra **dorada** es el nodo que se está procesando en ese paso. "
        "Las barras **grises** son nodos aún no alcanzados (∞)."
    )

    steps = dijkstra_with_steps(graph, source_id)
    fig2 = build_dijkstra_steps_chart(steps, graph)
    st.plotly_chart(fig2, use_container_width=True)

    # Tabla de ruta final
    if dij_path:
        st.markdown("#### Ruta óptima calculada")
        rows = []
        cumulative = 0
        for i, nid in enumerate(dij_path):
            node = graph.get_node(nid)
            if i == 0:
                latency_step = 0
            else:
                prev_nid = dij_path[i-1]
                for (nb, lat_ms, _) in graph.get_neighbors(prev_nid):
                    if nb == nid:
                        latency_step = lat_ms
                        break
            cumulative += latency_step if i > 0 else 0
            rows.append({
                "Salto": i,
                "Nodo": node.name,
                "Tipo": node.node_type,
                "Latencia paso (ms)": latency_step if i > 0 else "—",
                "Latencia acumulada (ms)": cumulative,
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**¿Por qué Dijkstra y no BFS?**")
    st.markdown(
        "BFS minimiza **saltos** (hops), no latencia. "
        "Dijkstra minimiza la **suma de pesos** en el camino. "
        "Con latencias distintas por arista, BFS puede dar rutas lentas con pocos saltos."
    )
    col1, col2 = st.columns(2)
    col1.metric("Complejidad Dijkstra", "O((V+E) log V)", "con min-heap")
    col2.metric("Complejidad BFS", "O(V+E)", "pero no minimiza latencia")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Prim MST
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🌿 Prim — Red de Fibra de Costo Mínimo (MST)")

    col_a, col_b, col_c = st.columns(3)
    all_edge_cost = sum(c for (_, _, _, c) in graph.get_all_edges())
    col_a.metric("Costo MST", f"${mst_cost:,.0f} USD", "red mínima")
    col_b.metric("Costo total de red", f"${all_edge_cost:,.0f} USD", "todos los cables")
    col_c.metric("Ahorro", f"${all_edge_cost - mst_cost:,.0f} USD",
                 f"{((all_edge_cost-mst_cost)/all_edge_cost*100):.0f}% menos")

    st.markdown("#### Aristas del MST")
    mst_rows = []
    for i, e in enumerate(mst_edges, 1):
        try:
            src_name = graph.get_node(e.source).name
            tgt_name = graph.get_node(e.target).name
        except KeyError:
            src_name, tgt_name = e.source, e.target
        mst_rows.append({
            "#": i,
            "Origen": src_name,
            "Destino": tgt_name,
            "Latencia (ms)": e.latency_ms,
            "Costo (USD)": f"${e.cost_usd:,.0f}",
        })
    df_mst = pd.DataFrame(mst_rows)
    st.dataframe(df_mst, use_container_width=True, hide_index=True)

    # Gráfica de costo acumulado
    cumulative_costs = []
    acc = 0
    for e in mst_edges:
        acc += e.cost_usd
        cumulative_costs.append(acc)

    fig_cost = go.Figure()
    fig_cost.add_trace(go.Scatter(
        x=list(range(1, len(mst_edges)+1)),
        y=cumulative_costs,
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color="#2ecc71", width=2),
        marker=dict(size=7),
        name="Costo acumulado MST",
    ))
    fig_cost.add_hline(
        y=all_edge_cost,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"Costo total red: ${all_edge_cost:,.0f}",
        annotation_font_color="#e74c3c",
    )
    fig_cost.update_layout(
        title="Costo acumulado del MST vs costo total de la red",
        xaxis_title="Arista #",
        yaxis_title="Costo USD",
        paper_bgcolor="#faf8f4",
        plot_bgcolor="#f5f0e8",
        font=dict(color="#2c2416"),
        height=300,
    )
    st.plotly_chart(fig_cost, use_container_width=True)

    st.markdown("---")
    st.markdown("**¿Por qué Prim y no Kruskal?**")
    c1, c2 = st.columns(2)
    c1.metric("Prim", "O(E log V)", "eficiente en grafos densos")
    c2.metric("Kruskal", "O(E log E)", "mejor en grafos dispersos")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — KD-tree
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🔍 KD-tree — Servidor más cercano")

    servers = graph.get_nodes_by_type("server")

    col_x, col_y = st.columns([1, 1])
    with col_x:
        st.markdown(f"**Cliente en:** `({client_lat:.4f}, {client_lon:.4f})`")
        st.success(f"✅ Servidor más cercano: **{nearest.name}** ({dist_km:.3f} km)")

        st.markdown("#### Distancia a todos los servidores")
        server_rows = []
        for s in sorted(servers, key=lambda x: _haversine_dist(client_lat, client_lon, x.lat, x.lon)):
            d = _haversine_dist(client_lat, client_lon, s.lat, s.lon)
            server_rows.append({
                "Servidor": s.name,
                "Distancia (km)": round(d, 3),
                "Lat": s.lat,
                "Lon": s.lon,
                "Seleccionado": "⭐" if s.node_id == nearest.node_id else "",
            })
        df_srv = pd.DataFrame(server_rows)
        st.dataframe(df_srv, use_container_width=True, hide_index=True)

    with col_y:
        # Mini mapa solo con servidores y cliente
        fig_kd = go.Figure()
        for s in servers:
            is_nearest = s.node_id == nearest.node_id
            fig_kd.add_trace(go.Scatter(
                x=[s.lon], y=[s.lat],
                mode="markers+text",
                marker=dict(
                    size=22 if is_nearest else 14,
                    color="#ffd700" if is_nearest else "#e74c3c",
                    symbol="star" if is_nearest else "square",
                    line=dict(color="#fff", width=1.5),
                ),
                text=[s.name.split("-",1)[-1]],
                textposition="top center",
                textfont=dict(color="#ffd700" if is_nearest else "#e74c3c", size=10),
                name=s.name,
                showlegend=False,
                hovertemplate=f"<b>{s.name}</b><br>Lat:{s.lat}<br>Lon:{s.lon}<extra></extra>",
            ))
            # Línea de distancia al cliente
            fig_kd.add_trace(go.Scatter(
                x=[client_lon, s.lon], y=[client_lat, s.lat],
                mode="lines",
                line=dict(
                    color="#ffd700" if is_nearest else "#3a3a5c",
                    width=2.5 if is_nearest else 0.8,
                    dash="solid" if is_nearest else "dot",
                ),
                showlegend=False,
                hoverinfo="skip",
            ))
        # Cliente
        fig_kd.add_trace(go.Scatter(
            x=[client_lon], y=[client_lat],
            mode="markers+text",
            marker=dict(size=16, color="#00bcd4", symbol="cross",
                        line=dict(color="#fff", width=2)),
            text=["Cliente"],
            textposition="bottom center",
            textfont=dict(color="#00bcd4", size=10),
            name="Cliente",
            hovertemplate=f"Cliente<br>({client_lat:.4f}, {client_lon:.4f})<extra></extra>",
        ))
        fig_kd.update_layout(
            paper_bgcolor="#faf8f4", plot_bgcolor="#f5f0e8",
            font=dict(color="#2c2416"),
            height=380, showlegend=False,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(gridcolor="#e8e0d0"),
            yaxis=dict(gridcolor="#e8e0d0", scaleanchor="x", scaleratio=1),
        )
        st.plotly_chart(fig_kd, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("KD-tree build", "O(n log n)", "construcción del árbol")
    c2.metric("KD-tree búsqueda", "O(log n) prom", "vs O(n) búsqueda lineal")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — HashMap
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### #️⃣ HashMap — Índice O(1) de nodos")

    hm = graph.node_index

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Entradas", len(hm))
    col_b.metric("Capacidad", hm._capacity, "buckets")
    col_c.metric("Factor de carga", f"{hm._load_factor():.3f}", "umbral: 0.75")
    col_d.metric("Rehash en", f"{int(hm._capacity * 0.75)} entradas")

    # Búsqueda en vivo
    st.markdown("#### 🔎 Búsqueda en vivo por nombre")
    search_name = st.text_input(
        "Nombre del nodo (ej: Router-Reforma, Servidor-Central)",
        value="Router-Reforma",
        placeholder="Escribe un nombre...",
    )
    if search_name:
        t0 = time.perf_counter()
        try:
            found = graph.get_node_by_name(search_name)
            t1 = time.perf_counter()
            elapsed_us = (t1 - t0) * 1e6
            st.success(
                f"✅ Encontrado en **{elapsed_us:.2f} µs**  |  "
                f"`{found.node_id}` · {found.name} · {found.node_type} · "
                f"({found.lat}, {found.lon})"
            )
        except KeyError:
            st.error(f"❌ '{search_name}' no encontrado. Nodos disponibles:")
            st.write([n.name for n in graph.get_all_nodes()])

    # Benchmark O(1) vs O(n)
    st.markdown("#### 📊 Benchmark: HashMap O(1) vs Búsqueda Lineal O(n)")
    st.markdown(
        "Tiempos reales medidos en tu máquina. "
        "Cada punto es el promedio de 500 búsquedas."
    )
    with st.spinner("Ejecutando benchmark..."):
        fig_bench = build_complexity_chart()
    st.plotly_chart(fig_bench, use_container_width=True)

    # Distribución de buckets
    st.markdown("#### 🪣 Distribución de buckets (separate chaining)")
    bucket_data = []
    for i, bucket in enumerate(hm._buckets):
        chain_len = 0
        entry = bucket
        while entry is not None:
            chain_len += 1
            entry = entry.next_entry
        if chain_len > 0:
            bucket_data.append({"Bucket": i, "Longitud de cadena": chain_len})

    if bucket_data:
        df_buckets = pd.DataFrame(bucket_data)
        fig_buckets = go.Figure(go.Bar(
            x=df_buckets["Bucket"].astype(str),
            y=df_buckets["Longitud de cadena"],
            marker_color="#5b8dd9",
            text=df_buckets["Longitud de cadena"],
            textposition="outside",
        ))
        fig_buckets.update_layout(
            title="Entradas por bucket (solo buckets no vacíos)",
            xaxis_title="Bucket #",
            yaxis_title="Longitud de cadena",
            paper_bgcolor="#faf8f4",
            plot_bgcolor="#f5f0e8",
            font=dict(color="#2c2416"),
            height=280,
            showlegend=False,
        )
        st.plotly_chart(fig_buckets, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Complejidad y guía
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("### 📋 Tabla de complejidades")

    complexity_data = [
        {"Módulo": "HashMap", "Operación": "put / get / remove", "Tiempo": "O(1) prom", "Espacio": "O(n)", "Nota": "O(n) peor caso (todas colisionan)"},
        {"Módulo": "HashMap", "Operación": "rehash", "Tiempo": "O(n)", "Espacio": "O(n)", "Nota": "Ocurre cuando load factor ≥ 0.75"},
        {"Módulo": "Graph", "Operación": "add_node / add_edge", "Tiempo": "O(1)", "Espacio": "O(1)", "Nota": "Lista de adyacencia"},
        {"Módulo": "Graph", "Operación": "get_neighbors", "Tiempo": "O(1)", "Espacio": "—", "Nota": "Lookup en HashMap"},
        {"Módulo": "Dijkstra", "Operación": "ruta completa", "Tiempo": "O((V+E) log V)", "Espacio": "O(V)", "Nota": "Con min-heap"},
        {"Módulo": "Prim", "Operación": "MST completo", "Tiempo": "O(E log V)", "Espacio": "O(V+E)", "Nota": "Con min-heap"},
        {"Módulo": "KD-tree", "Operación": "build", "Tiempo": "O(n log n)", "Espacio": "O(n)", "Nota": "Ordenar en cada nivel"},
        {"Módulo": "KD-tree", "Operación": "nearest_neighbor", "Tiempo": "O(log n) prom", "Espacio": "O(log n)", "Nota": "O(n) peor caso: datos lineales"},
    ]
    df_c = pd.DataFrame(complexity_data)
    st.dataframe(df_c, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🎤 Guía de presentación — 10 minutos")

    steps_pres = [
        ("0:00–0:45", "Introducción", "El problema ISP: latencia, fibra, geolocalización. Variante 4."),
        ("0:45–2:00", "Arquitectura", "Mostrar diagrama en ARCHITECTURE.md. Flujo de datos."),
        ("2:00–3:30", "Tab HashMap", "Búsqueda en vivo + benchmark O(1) vs O(n) + distribución de buckets."),
        ("3:30–5:00", "Tab KD-tree", "Cambiar coordenadas GPS, ver servidor actualizado, mini-mapa."),
        ("5:00–6:30", "Tab Dijkstra", "Animación paso a paso, tabla de saltos, latencia final."),
        ("6:30–8:00", "Tab Prim MST", "Tabla de aristas, gráfica de costo acumulado, ahorro vs red completa."),
        ("8:00–9:00", "Tab Red ISP", "Mapa interactivo completo: zoom, hover, todos los algoritmos juntos."),
        ("9:00–10:00", "Tab Complejidad", "Tabla de complejidades + preguntas del profesor."),
    ]
    for tiempo, seccion, descripcion in steps_pres:
        with st.expander(f"⏱️ {tiempo} — {seccion}"):
            st.write(descripcion)

    st.markdown("---")
    st.markdown("### ❓ Preguntas frecuentes del profesor")

    faqs = {
        "¿Por qué HashMap y no el dict de Python?": (
            "El dict de Python es una tabla hash, pero no controlamos la función hash, "
            "la resolución de colisiones ni el rehashing. Nuestro HashMap usa djb2 "
            "con separate chaining y rehash automático al 0.75 de factor de carga. "
            "Podemos explicar cada decisión de diseño con detalle."
        ),
        "¿Dijkstra funciona con pesos negativos?": (
            "No. Requiere pesos ≥ 0. Nuestras latencias siempre son positivas. "
            "Para pesos negativos usaríamos Bellman-Ford: O(VE) vs nuestro O((V+E) log V). "
            "En nuestra red Dijkstra es correcto y más eficiente."
        ),
        "¿Por qué Prim y no Kruskal?": (
            "Prim: O(E log V) — crece desde un nodo con min-heap. "
            "Kruskal: O(E log E) — ordena todas las aristas + Union-Find. "
            "En grafos densos (muchas conexiones por nodo) Prim es más eficiente. "
            "Prim también es más natural para redes que se expanden gradualmente."
        ),
        "¿El KD-tree está balanceado?": (
            "Sí. Al construir, en cada nivel ordenamos por el eje actual (lat o lon) "
            "y elegimos el mediano como raíz. Esto garantiza profundidad O(log n). "
            "El peor caso de búsqueda es O(n) si los puntos están todos alineados, "
            "pero con coordenadas GPS geográficas eso no ocurre en la práctica."
        ),
        "¿Por qué separate chaining y no open addressing?": (
            "Separate chaining es más predecible con strings similares. "
            "Con factor de carga < 0.75, el promedio es O(1). "
            "Open addressing con linear probing sufre clustering primario "
            "que degrada las búsquedas incluso con factor de carga moderado."
        ),
    }
    for pregunta, respuesta in faqs.items():
        with st.expander(f"❓ {pregunta}"):
            st.write(respuesta)
