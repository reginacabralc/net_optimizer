# 🌐 NetOptimizer

**Simulador de red de fibra óptica para ISP — Variante 4**  
Proyecto Final · Estructuras de Datos y Algoritmos

---

## El problema

Una ISP necesita resolver tres problemas simultáneamente:

1. **¿Por qué ruta llega antes el paquete?** → Minimizar latencia entre usuario y servidor.
2. **¿Cómo tiendo el menor cable posible?** → Red de fibra de costo mínimo que conecte todos los nodos.
3. **¿A qué servidor conecto este nuevo cliente?** → Servidor más cercano geográficamente.

NetOptimizer resuelve los tres con algoritmos implementados manualmente sobre una red simulada de 18 nodos en Ciudad de México.

---

## Demo rápido

```bash
git clone <repo-url>
cd netoptimizer
pip install -r requirements.txt
python src/demo.py
```

Con coordenadas personalizadas:

```bash
python src/demo.py --lat 19.4334 --lon -99.1945
```

Salida esperada:

```
══════════════════════════════════════════════════════════
  🌐  NetOptimizer — ISP Network Optimizer
      Variante 4 | Estructuras de Datos y Algoritmos
══════════════════════════════════════════════════════════

PASO 1 — Cargando red ISP desde CSV
  18 nodos cargados | 26 aristas cargadas

PASO 2 — HashMap propio (índice O(1) de nodos)
  Entradas: 18 | Factor de carga: 0.281 | Cadena máx: 3

PASO 3 — KD-tree: servidor más cercano
  Nuevo cliente en: (19.4326, -99.1332)
  Servidor más cercano: Servidor-Central (4.65 km)

PASO 4 — Dijkstra: ruta de menor latencia
  Ruta: Usuario-Coyoacan → Switch-Tasquena → Servidor-Central
  Latencia total: 13.0 ms | Saltos: 2

PASO 5 — Prim: red de fibra de costo mínimo
  Aristas MST: 17 | Costo total: $153,500 USD

[abre ventana con gráfico de la red]
```

---

## Estructuras de datos implementadas

Todas implementadas **manualmente**, sin librerías que las resuelvan.

| Estructura | Archivo | Descripción |
|---|---|---|
| **HashMap** (separate chaining) | `src/hash_map.py` | Índice de nodos O(1) por ID y nombre |
| **Grafo** (lista de adyacencia) | `src/graph.py` | Red de nodos y conexiones con dos pesos |
| **KD-tree 2D** | `src/kdtree.py` | Búsqueda del servidor más cercano por GPS |
| **Min-Heap** (via `heapq`) | `src/dijkstra.py`, `src/prim.py` | Selección greedy en Dijkstra y Prim |

---

## Algoritmos implementados

| Algoritmo | Archivo | Peso usado | Complejidad |
|---|---|---|---|
| **Dijkstra** | `src/dijkstra.py` | `latency_ms` | O((V+E) log V) |
| **Prim MST** | `src/prim.py` | `cost_usd` | O(E log V) |
| **KD-tree build** | `src/kdtree.py` | — | O(n log n) |
| **KD-tree nearest** | `src/kdtree.py` | distancia GPS | O(log n) prom |
| **HashMap put/get** | `src/hash_map.py` | — | O(1) prom |

---

## Justificación de la estructura adicional: HashMap

Se eligió **HashMap propio con separate chaining** como estructura adicional porque:

- Se integra de forma natural como índice del grafo (`node_id → Node`, `name → node_id`)
- Permite comparación directa contra búsqueda lineal en el demo
- Es la diferencia más visible y explicable en una presentación de 10 minutos

**Comparación de complejidad:**

| Operación | HashMap (nuestro) | Lista / array |
|---|---|---|
| Buscar por nombre | O(1) promedio | O(n) |
| Insertar | O(1) amortizado | O(1) |
| Eliminar | O(1) promedio | O(n) |
| Espacio | O(n) | O(n) |

Con 18 nodos la diferencia es pequeña, pero el argumento escala: con 10,000 nodos el HashMap sigue siendo O(1), la lista sería 10,000 comparaciones por búsqueda.

**Detalles de implementación:**
- Función hash: variante djb2 (`h = h * 33 ^ ord(c)`)
- Resolución de colisiones: separate chaining con listas enlazadas
- Rehash automático cuando `load_factor >= 0.75` (duplica capacidad)
- Capacidad inicial: 64 buckets

---

## Instalación

**Requisitos:** Python 3.9+

```bash
git clone <repo-url>
cd netoptimizer
pip install -r requirements.txt
```

Dependencias (`requirements.txt`):
```
matplotlib>=3.5.0
pandas>=1.3.0
```

No se usan NetworkX, sklearn, scipy ni ninguna librería que implemente los algoritmos.

---

## Cómo correr

```bash
# Demo completo (recomendado para la presentación)
python src/demo.py

# Con coordenadas GPS personalizadas
python src/demo.py --lat 19.4326 --lon -99.1332

# Modo interactivo (menú)
python src/main.py
```

## Cómo correr los tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Por módulo
python -m pytest tests/test_dijkstra.py -v
python -m pytest tests/test_prim.py -v
python -m pytest tests/test_kdtree.py -v
python -m pytest tests/test_hash_map.py -v
```

Resultado esperado: **76 tests, 0 fallos.**

---

## Estructura del repositorio

```
netoptimizer/
│
├── README.md               ← este archivo
├── CLAUDE.md               ← guía para agentes IA
├── AGENTS.md               ← división de trabajo L y R
├── ARCHITECTURE.md         ← arquitectura y decisiones de diseño
├── DATA.md                 ← documentación de los datos
├── PHASES.md               ← plan de ejecución en 2 días
├── PROGRESS.md             ← tracker de avance
├── requirements.txt
│
├── data/
│   ├── nodes.csv           ← 18 nodos: servidores, routers, switches, usuarios
│   └── edges.csv           ← 26 aristas con latencia (ms) y costo (USD)
│
├── src/
│   ├── __init__.py
│   ├── models.py           ← dataclasses Node y Edge
│   ├── hash_map.py         ← HashMap propio (separate chaining)
│   ├── graph.py            ← grafo con lista de adyacencia + HashMap
│   ├── dijkstra.py         ← Dijkstra manual (ruta de menor latencia)
│   ├── prim.py             ← Prim MST manual (red de fibra de costo mínimo)
│   ├── kdtree.py           ← KD-tree 2D manual (servidor más cercano)
│   ├── data_loader.py      ← carga CSV → objetos Graph
│   ├── visualize.py        ← visualización con matplotlib
│   ├── demo.py             ← ENTRY POINT del demo
│   └── main.py             ← modo interactivo con menú
│
└── tests/
    ├── __init__.py
    ├── test_hash_map.py    ← 19 tests para HashMap
    ├── test_dijkstra.py    ← 16 tests para Dijkstra
    ├── test_prim.py        ← 13 tests para Prim
    └── test_kdtree.py      ← 24 tests para KD-tree
```

---

## Red simulada

18 nodos en Ciudad de México con coordenadas GPS reales:

| Tipo | Cantidad | Ejemplos |
|---|---|---|
| Servidores | 5 | Central (Benito Juárez), Norte (GAM), Sur (Xochimilco), Oriente (Iztapalapa), Poniente (Álvaro Obregón) |
| Routers | 5 | Reforma, Insurgentes, Periférico Norte, Indios Verdes, Pantitlán |
| Switches | 3 | Observatorio, Tasqueña, Xochimilco |
| Usuarios | 5 | Polanco, Coyoacán, Santa Fe, Ecatepec, Tlalpan |

26 conexiones con:
- `latency_ms`: entre 2 y 18 ms (peso para Dijkstra)
- `cost_usd`: entre $4,000 y $20,000 USD (peso para Prim)

---

## Visualización

El demo genera un gráfico matplotlib con:

| Elemento | Visual |
|---|---|
| Servidores | Cuadrado rojo |
| Routers | Círculo azul |
| Switches | Diamante naranja |
| Usuarios | Triángulo verde |
| Servidor más cercano | Estrella dorada (KD-tree) |
| Nuevo cliente | Cruz cian |
| MST (Prim) | Líneas verdes gruesas |
| Ruta Dijkstra | Líneas rojas con flechas |
| Fondo de red | Líneas grises |

---

## Complejidad completa

| Módulo | Operación | Tiempo | Espacio |
|---|---|---|---|
| HashMap | `put` / `get` | O(1) prom | O(n) |
| HashMap | rehash | O(n) | O(n) |
| Graph | `add_node` | O(1) | O(1) |
| Graph | `add_edge` | O(1) | O(1) |
| Graph | `get_neighbors` | O(1) | — |
| Dijkstra | ruta completa | O((V+E) log V) | O(V) |
| Prim | MST completo | O(E log V) | O(V+E) |
| KD-tree | `build` | O(n log n) | O(n) |
| KD-tree | `nearest_neighbor` | O(log n) prom | O(log n) |

---

## Guía de presentación — 10 minutos

| Tiempo | Sección | Qué mostrar |
|---|---|---|
| 0:00–0:45 | Introducción | El problema ISP, la variante 4, el repo |
| 0:45–2:00 | Arquitectura | `ARCHITECTURE.md`, diagrama ASCII, flujo de datos |
| 2:00–3:30 | HashMap | `hash_map.py` líneas 1–60, tabla O(1) vs O(n), stats en demo |
| 3:30–5:00 | KD-tree | `kdtree.py` método `_build_recursive`, correr paso 3 del demo |
| 5:00–6:30 | Dijkstra | `dijkstra.py` el while principal, correr paso 4 del demo |
| 6:30–8:00 | Prim | `prim.py` el while principal, correr paso 5 del demo, mostrar ahorro |
| 8:00–9:00 | Visualización | Abrir el gráfico, señalar cada elemento |
| 9:00–10:00 | Tests y cierre | `pytest tests/ -v`, tabla de complejidades, conclusión |

---

## Preguntas frecuentes del profesor

**¿Por qué HashMap y no el dict de Python?**
El dict de Python es una tabla hash, pero no controlamos la función hash, la resolución de colisiones ni el rehashing. Nuestro HashMap usa djb2 con separate chaining y rehash automático a 0.75 de factor de carga, lo que nos permite explicar cada decisión de diseño.

**¿Dijkstra funciona con pesos negativos?**
No. Requiere pesos ≥ 0. Nuestras latencias siempre son positivas, así que es correcto. Para pesos negativos existiría Bellman-Ford: O(VE) vs nuestro O((V+E) log V).

**¿Por qué Prim y no Kruskal?**
Prim es O(E log V) con heap; Kruskal es O(E log E) con Union-Find. En redes densas (muchas conexiones) Prim es más eficiente. Además, Prim crece desde un nodo, lo que es conceptualmente más natural para una red ISP que va expandiéndose.

**¿El KD-tree está balanceado?**
Sí. Al construir, en cada nivel se ordena por el eje actual y se toma el mediano como raíz. Esto garantiza profundidad O(log n). El peor caso de búsqueda es O(n) si los puntos están alineados, pero con coordenadas GPS reales no ocurre.

**¿Por qué separate chaining y no open addressing?**
Separate chaining es más predecible con strings similares. El peor caso (toda la cadena en un bucket) es O(n), pero el promedio con load factor < 0.75 es O(1). Open addressing con linear probing sufre de clustering primario que degrada el promedio.

**¿Por qué lista de adyacencia y no matriz?**
Una red ISP es dispersa: cada nodo tiene 2–5 vecinos, no N. La lista de adyacencia usa O(V+E) de memoria vs O(V²) de la matriz. Dijkstra y Prim iteran sobre vecinos de cada nodo, no sobre todos los nodos posibles.
