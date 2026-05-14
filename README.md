# 🌐 NetOptimizer

**Simulador de red de fibra óptica para ISP**  
Proyecto Final · Estructuras de Datos y Algoritmos · Variante 4

---

```
╔══════════════════════════════════════════════════════════════╗
║  KD-tree → servidor más cercano    O(log n)                 ║
║  Dijkstra → ruta de menor latencia O((V+E) log V)           ║
║  Prim MST → fibra de costo mínimo  O(E log V)               ║
║  HashMap  → búsqueda de nodos      O(1) promedio            ║
╚══════════════════════════════════════════════════════════════╝
```

---

## El problema

Una ISP necesita resolver tres desafíos simultáneamente al conectar un nuevo cliente a su red de fibra óptica:

1. **¿A qué servidor lo conecto?** → Encontrar el servidor geográficamente más cercano
2. **¿Por qué ruta llega más rápido?** → Calcular el camino de menor latencia
3. **¿Cómo tiendo el menor cable posible?** → Red de fibra de costo mínimo

NetOptimizer resuelve los tres sobre una red simulada de **18 nodos en Ciudad de México**, con un dashboard interactivo que permite explorar cada algoritmo en tiempo real.

---

## Demo

```bash
git clone <repo-url>
cd netoptimizer
pip install -r requirements.txt
streamlit run app.py
```

Abre automáticamente en `http://localhost:8501`

---

## Dashboard

El dashboard tiene **6 tabs interactivos**:

| Tab | Contenido |
|---|---|
| 🗺️ **Red ISP** | Mapa Plotly zoomable con todos los algoritmos superpuestos. Hover sobre nodos para ver detalles |
| ⚡ **Dijkstra paso a paso** | Animación con slider que muestra cómo se actualizan las distancias mínimas en cada iteración |
| 🌿 **Prim MST** | Tabla de aristas del árbol + gráfica de costo acumulado vs costo total de la red |
| 🔍 **KD-tree** | Mini-mapa con líneas de distancia a todos los servidores + tabla ordenada por cercanía |
| #️⃣ **HashMap** | Búsqueda en vivo con tiempo en µs + benchmark real O(1) vs O(n) + distribución de buckets |
| 📋 **Complejidad** | Tabla comparativa de algoritmos + guía de presentación + FAQs del profesor |

**Sidebar:** coordenadas GPS editables, toggles por algoritmo, selector de nodo origen para Dijkstra. Todo actualiza el mapa en tiempo real.

---

## Algoritmos implementados

> Todos implementados **manualmente** desde cero. Sin NetworkX, sin sklearn, sin scipy.

### 🔵 Dijkstra — Ruta de menor latencia

Encuentra el camino de menor latencia (ms) entre cualquier par de nodos usando un min-heap.

```
Complejidad: O((V + E) log V)    Espacio: O(V)
Peso usado:  latency_ms
```

**¿Por qué Dijkstra y no BFS?**
BFS minimiza saltos, no latencia. Con pesos distintos por arista, BFS puede elegir rutas de pocos saltos pero alta latencia. Dijkstra garantiza el óptimo mientras los pesos sean ≥ 0.

**¿Por qué no Bellman-Ford?**
Bellman-Ford soporta pesos negativos → O(VE). Las latencias en nuestra red son siempre positivas, por lo que Dijkstra es correcto y más eficiente.

El dashboard incluye animación paso a paso que muestra cómo cada nodo actualiza sus distancias hasta que el frente de onda alcanza el destino.

---

### 🟢 Prim — Red de fibra de costo mínimo (MST)

Construye el Árbol de Expansión Mínima que conecta todos los nodos con el menor costo total de instalación de fibra.

```
Complejidad: O(E log V)    Espacio: O(V + E)
Peso usado:  cost_usd
```

**¿Por qué Prim y no Kruskal?**

| | Prim | Kruskal |
|---|---|---|
| Complejidad | O(E log V) | O(E log E) |
| Estrategia | Crece desde un nodo | Ordena todas las aristas |
| Mejor en | Grafos densos | Grafos dispersos |
| Auxiliar | Min-heap | Union-Find |

---

### 🟡 KD-tree 2D — Servidor más cercano

Árbol binario que divide el espacio geográfico (lat, lon) para encontrar el servidor más cercano a cualquier coordenada GPS.

```
Build:    O(n log n)       Espacio: O(n)
Búsqueda: O(log n) prom   Distancia: fórmula Haversine (km reales)
```

**¿Por qué KD-tree y no búsqueda lineal?**

| Servidores | Búsqueda lineal | KD-tree |
|---|---|---|
| 5 | 5 ops | ~3 ops |
| 1,000 | 1,000 ops | ~10 ops |
| 1,000,000 | 1,000,000 ops | ~20 ops |

---

### 🔴 HashMap — Índice O(1) de nodos

Tabla hash con **separate chaining** que indexa todos los nodos por `node_id` y por `name`. Es el pegamento del sistema: el grafo lo usa internamente para su lista de adyacencia.

```
put / get / remove: O(1) promedio
Función hash: djb2  →  h = h * 33 ^ ord(c)
Rehash automático cuando load_factor ≥ 0.75
Capacidad inicial: 64 buckets
```

**Benchmark real medido en ejecución:**

```
n = 10,000 elementos
HashMap:          ~0.15 µs   (O(1))
Búsqueda lineal:  ~82.3 µs   (O(n))
Speedup:          ~550×
```

---

## Estructura de datos del grafo

```
Graph
├── _nodes:      HashMap[node_id → Node]
├── _name_index: HashMap[name → node_id]
└── _adj:        HashMap[node_id → List[(neighbor_id, latency_ms, cost_usd)]]
```

**Lista de adyacencia vs matriz:** La red ISP es dispersa (2–5 vecinos por nodo).
La lista usa O(V+E); la matriz usaría O(V²). Con 10,000 nodos: 50,000 entradas vs 100 millones.

---

## Red simulada — Ciudad de México

18 nodos con coordenadas GPS reales:

```
Servidores (5)                  Routers (5)
────────────────────────        ────────────────────────────
S01  Servidor-Central           R01  Router-Reforma
S02  Servidor-Norte             R02  Router-Insurgentes
S03  Servidor-Sur               R03  Router-Periferico-Norte
S04  Servidor-Oriente           R04  Router-Indios-Verdes
S05  Servidor-Poniente          R05  Router-Pantitlan

Switches (3)                    Usuarios (5)
────────────────────────        ────────────────────────────
SW01 Switch-Observatorio        U01  Usuario-Polanco
SW02 Switch-Tasquena            U02  Usuario-Coyoacan
SW03 Switch-Xochimilco          U03  Usuario-Santa-Fe
                                U04  Usuario-Ecatepec
                                U05  Usuario-Tlalpan
```

26 conexiones: `latency_ms` entre 2–18 ms · `cost_usd` entre $4,000–$20,000

---

## Instalación

**Requisitos:** Python 3.9+

```bash
git clone <repo-url>
cd netoptimizer
pip install -r requirements.txt
streamlit run app.py
```

```
streamlit>=1.28.0    # dashboard web
plotly>=5.15.0       # gráficas interactivas
matplotlib>=3.5.0    # visualización alternativa
pandas>=1.3.0        # carga de CSV
```

---

## Comandos

```bash
streamlit run app.py                          # dashboard (presentación)
python src/demo.py                            # demo consola + matplotlib
python src/demo.py --lat 19.43 --lon -99.18  # coordenadas personalizadas
python src/main.py                            # menú interactivo
python -m pytest tests/ -v                   # 76 tests
```

---

## Estructura del repositorio

```
netoptimizer/
├── app.py                  ← ENTRY POINT: streamlit run app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── nodes.csv           ← 18 nodos (tipo + coordenadas GPS)
│   └── edges.csv           ← 26 aristas (latency_ms + cost_usd)
│
├── src/
│   ├── models.py           ← dataclasses Node y Edge
│   ├── hash_map.py         ← HashMap: separate chaining + rehash
│   ├── graph.py            ← grafo con lista de adyacencia + HashMap
│   ├── dijkstra.py         ← Dijkstra + dijkstra_with_steps() (animación)
│   ├── prim.py             ← Prim MST
│   ├── kdtree.py           ← KD-tree 2D + Haversine
│   ├── data_loader.py      ← CSV → Graph
│   ├── visualize_plotly.py ← figuras Plotly para el dashboard
│   ├── visualize.py        ← matplotlib (demo.py)
│   ├── demo.py             ← demo consola alternativo
│   └── main.py             ← menú interactivo
│
└── tests/
    ├── test_hash_map.py    ← 19 tests
    ├── test_dijkstra.py    ← 16 tests
    ├── test_prim.py        ← 13 tests
    └── test_kdtree.py      ← 24 tests (incluye validación vs fuerza bruta)
```

---

## Complejidad comparativa

| Módulo | Operación | Tiempo | Espacio |
|---|---|---|---|
| HashMap | `put` / `get` / `remove` | **O(1) prom** | O(n) |
| HashMap | rehash | O(n) | O(n) |
| Búsqueda lineal | por nombre | O(n) | O(1) |
| Graph | `add_node` / `add_edge` | O(1) | O(1) |
| Graph | `get_neighbors` | O(1) | — |
| **Dijkstra** | ruta completa | **O((V+E) log V)** | O(V) |
| Bellman-Ford | ruta completa | O(VE) | O(V) |
| BFS | mínimos saltos | O(V+E) | O(V) |
| **Prim** | MST completo | **O(E log V)** | O(V+E) |
| Kruskal | MST completo | O(E log E) | O(V) |
| **KD-tree** | build | O(n log n) | O(n) |
| **KD-tree** | `nearest_neighbor` | **O(log n) prom** | O(log n) |

---

## Preguntas frecuentes del profesor

<details>
<summary><b>¿Por qué HashMap y no el dict de Python?</b></summary>

El `dict` de Python es una tabla hash optimizada en C. Nuestro `HashMap` permite discutir y demostrar cada decisión: función hash djb2, separate chaining, factor de carga 0.75, rehashing. El tab HashMap del dashboard muestra tiempos reales en µs y la distribución de buckets.

</details>

<details>
<summary><b>¿Por qué separate chaining y no open addressing?</b></summary>

Separate chaining es más predecible con strings similares. Con load factor < 0.75 el promedio es O(1). Open addressing sufre clustering primario: colisiones cercanas provocan que búsquedas siguientes también colisionen, degradando el promedio incluso con carga moderada.

</details>

<details>
<summary><b>¿Dijkstra funciona con pesos negativos?</b></summary>

No. Dijkstra asume que agregar una arista nunca reduce el costo acumulado, lo que solo es verdad con pesos ≥ 0. Latencias y costos en nuestra red siempre son positivos → Dijkstra es correcto. Para negativos: Bellman-Ford O(VE) vs nuestro O((V+E) log V).

</details>

<details>
<summary><b>¿Por qué Prim y no Kruskal?</b></summary>

Prim crece desde un nodo con min-heap → O(E log V). Kruskal ordena todas las aristas + Union-Find → O(E log E). En grafos densos (E ≈ V²) Prim es más eficiente. Además mantiene el árbol conexo en todo momento, más natural para una red ISP que se expande gradualmente.

</details>

<details>
<summary><b>¿El KD-tree está balanceado?</b></summary>

Sí. En cada nivel se ordena por el eje actual y se elige el mediano → ambos subárboles tienen igual cantidad de puntos → profundidad O(log n). Peor caso O(n) solo si todos los puntos están alineados, lo que no ocurre con GPS reales.

</details>

<details>
<summary><b>¿Por qué Haversine y no distancia euclídea?</b></summary>

El KD-tree usa euclídea internamente para las comparaciones (rápido, sin trigonometría). Solo al reportar el resultado final usamos Haversine para obtener kilómetros reales con curvatura terrestre. Para CDMX (~100km de radio) la diferencia es menor al 1%, pero el reporte en km es más útil para el usuario.

</details>

---

## Guía de presentación — 10 minutos

| Tiempo | Qué hacer |
|---|---|
| 0:00–0:45 | Problema ISP, variante 4, abrir el dashboard |
| 0:45–1:45 | Sidebar: cambiar lat/lon, mostrar que todo actualiza en vivo |
| 1:45–3:00 | Tab HashMap: búsqueda en µs, benchmark O(1) vs O(n), distribución de buckets |
| 3:00–4:15 | Tab KD-tree: mini-mapa, cambiar coordenadas, ver servidor cambiar |
| 4:15–5:45 | Tab Dijkstra: animación paso a paso, tabla de saltos y latencia |
| 5:45–7:00 | Tab Prim MST: aristas, gráfica de ahorro, comparar con Kruskal |
| 7:00–8:15 | Tab Red ISP: mapa completo, zoom, hover, toggle de capas |
| 8:15–9:15 | Tab Complejidad: tabla comparativa |
| 9:15–10:00 | `pytest tests/ -v` → 76 passed. Preguntas |

---

*Proyecto desarrollado en 2 días · Equipo L & R · Estructuras de Datos y Algoritmos*
