# NetOptimizer — Red de Internet / Telecomunicaciones
## Regina Cabral y Luciano Ramírez

NetOptimizer es un proyecto de estructuras de datos para la **Variante 4: Red de Internet / Telecomunicaciones**. Modela una red pequeña de fibra óptica de un ISP en Ciudad de México y muestra cómo los algoritmos clásicos resuelven problemas reales de optimización:

- ¿Cuál es la **ruta de menor latencia** desde una zona de usuarios hasta un centro de datos?
- ¿Cuál es la **red troncal de fibra de menor costo** que conecta todos los nodos?
- ¿Qué centro de datos está **geográficamente más cerca** de un cliente nuevo?
- ¿Qué estructura de datos adicional mejora el rendimiento de las búsquedas?

El proyecto incluye módulos de algoritmos, datos CSV, pruebas unitarias, demo por consola, visualización con Matplotlib y panel interactivo con Streamlit.

## Requisitos de la Variante 4

| Requisito | Implementación del proyecto | Archivos principales |
|---|---|---|
| Dijkstra para ruta de menor latencia | Usa `latency_ms` como peso de arista y devuelve el camino con menor latencia total. | `src/dijkstra.py`, `src/graph.py` |
| Prim para red de fibra de costo mínimo | Usa `cost_usd` como peso de arista y devuelve el árbol de expansión mínima. | `src/prim.py`, `src/graph.py` |
| KD-tree para servidor más cercano | Construye un KD-tree 2D con coordenadas de servidores y localiza el más cercano a un cliente nuevo. | `src/kdtree.py` |
| Estructura adicional del curso | Implementa un `HashMap` propio con encadenamiento separado y lo usa dentro de `Graph` para índices por nodo y nombre. | `src/hash_map.py`, `src/graph.py` |
| Análisis comparativo de complejidad | Está documentado en módulos, pruebas, dashboard y este README. | `README.md`, `app.py` |

## Modelo de Datos

Los datos viven en archivos CSV dentro de `data/`.

### `data/nodes.csv`

| Columna | Significado |
|---|---|
| `node_id` | Identificador único del nodo. |
| `node_type` | Tipo técnico: `server`, `router`, `switch` o `user`. Se conserva en inglés porque es parte del contrato del código. |
| `name` | Nombre legible de la ubicación de red. |
| `lat` | Latitud en grados decimales. |
| `lon` | Longitud en grados decimales. |

### `data/edges.csv`

| Columna | Significado |
|---|---|
| `source` | ID del nodo origen. |
| `target` | ID del nodo destino. |
| `latency_ms` | Latencia del enlace en milisegundos. Es el criterio de optimización de Dijkstra. |
| `cost_usd` | Costo de instalación o despliegue de fibra. Es el criterio de optimización de Prim. |
| `bandwidth_gbps` | Capacidad del enlace en gigabits por segundo. Se muestra como metadato telecom en rutas y tablas, pero no reemplaza latencia ni costo como pesos requeridos. |

El grafo es no dirigido: cada arista del CSV se inserta en ambos sentidos dentro de la lista de adyacencia.

## Algoritmos y Estructuras

### Dijkstra — Menor Latencia

`src/dijkstra.py` implementa Dijkstra con `heapq` como cola de prioridad mínima.

- Entrada: grafo, nodo origen y nodo destino opcional.
- Peso usado: `latency_ms`.
- Salida: latencia mínima total y ruta.
- Justificación: BFS minimiza saltos, no latencia. Bellman-Ford permite pesos negativos, pero es más lento. Las latencias de telecomunicaciones son no negativas, así que Dijkstra es correcto y eficiente.

Complejidad:

- Tiempo: `O((V + E) log V)` con min-heap.
- Espacio: `O(V)` para distancias, predecesores, heap y nodos visitados.

### Prim — Red de Fibra de Costo Mínimo

`src/prim.py` implementa Prim con min-heap.

- Entrada: grafo y nodo inicial opcional.
- Peso usado: `cost_usd`.
- Salida: aristas del MST y costo total.
- Justificación: Prim crece una red conectada eligiendo siempre la arista más barata que alcanza un nodo nuevo. Esto encaja naturalmente con una historia de expansión de infraestructura ISP.

Complejidad:

- Tiempo: `O(E log V)`.
- Espacio: `O(V + E)`.

### KD-tree — Centro de Datos Más Cercano

`src/kdtree.py` implementa un KD-tree 2D sobre coordenadas `(lat, lon)` usando solo nodos de tipo `server`.

- Entrada: nodos servidor o centro de datos.
- Consulta: latitud y longitud del cliente nuevo.
- Salida: servidor más cercano y distancia en kilómetros.
- Justificación: una búsqueda lineal revisa todos los servidores: `O(n)`. El KD-tree divide el plano y logra búsqueda promedio `O(log n)`.

Complejidad:

- Construcción: `O(n log n)`.
- Búsqueda de vecino más cercano: `O(log n)` promedio, `O(n)` peor caso.
- Espacio: `O(n)`.

### HashMap — Estructura Adicional del Curso

`src/hash_map.py` implementa una tabla hash propia con:

- Función hash polinomial para strings.
- Encadenamiento separado para colisiones.
- Rehash automático cuando el factor de carga llega a `0.75`.

El grafo usa este HashMap para:

- `node_id -> Node`: obtener nodos por ID.
- `node_id -> lista de adyacencia`: obtener vecinos de un nodo.
- `name -> node_id`: buscar nodos por nombre legible.

Por qué se eligió HashMap:

| Operación | HashMap promedio | Lista lineal |
|---|---:|---:|
| Inserción | `O(1)` amortizado | `O(1)` |
| Búsqueda por ID/nombre | `O(1)` promedio | `O(n)` |
| Eliminación | `O(1)` promedio | `O(n)` |
| Peor caso de búsqueda | `O(n)` | `O(n)` |

En este proyecto, la operación más frecuente es la búsqueda exacta por ID o por nombre. Por eso un HashMap es más adecuado que un AVL, Skip List, Trie o Bloom Filter.

## Flujo del Backend

1. `src/data_loader.py` lee `nodes.csv` y `edges.csv`.
2. Valida columnas requeridas, incluyendo `bandwidth_gbps`.
3. Crea dataclasses inmutables `Node` y `Edge` desde `src/models.py`.
4. Inserta nodos y aristas en `Graph` desde `src/graph.py`.
5. `Graph` guarda nodos y listas de adyacencia dentro del `HashMap` propio.
6. Los algoritmos consumen el grafo mediante `get_neighbors()`, `get_all_nodes()` y filtros por tipo de nodo.

Operaciones importantes del grafo:

| Operación | Complejidad | Nota |
|---|---:|---|
| `add_node` | `O(1)` promedio | Inserción en HashMap. |
| `add_edge` | `O(1)` promedio | Agrega dos entradas porque el grafo es no dirigido. |
| `get_node` | `O(1)` promedio | Búsqueda en HashMap. |
| `get_node_by_name` | `O(1)` promedio | Usa índice por nombre en HashMap. |
| `get_neighbors` | `O(1)` promedio | Devuelve la lista de adyacencia. |
| `get_all_edges` | `O(V + E)` | Recorre adyacencias y evita duplicados. |

## Guía del Panel

Ejecutar con:

```bash
streamlit run app.py
```

El dashboard carga el grafo una vez con cache de Streamlit, construye el KD-tree con los servidores, calcula Dijkstra y Prim según las entradas seleccionadas y renderiza las vistas con Plotly.

### Barra Lateral

- Entrada: `Latitud` y `Longitud` del cliente nuevo.
- Entrada: casillas para mostrar MST, ruta Dijkstra y servidor más cercano en el mapa principal.
- Entrada: selector de nodo origen para Dijkstra.
- Backend usado: carga de grafo, búsqueda KD-tree, ruta Dijkstra y MST de Prim.

### Pestaña 1 — Red ISP

- Muestra el mapa completo de la red.
- Dibuja aristas base, nodos por tipo, ruta Dijkstra, MST de Prim, servidor más cercano y cliente nuevo.
- El mensaje emergente de enlaces muestra latencia, costo y `bandwidth_gbps`.
- Demuestra cómo todos los algoritmos trabajan sobre el mismo grafo.

### Pestaña 2 — Dijkstra Paso a Paso

- Entrada: nodo origen de la barra lateral; el destino es el centro de datos más cercano por KD-tree.
- Ejecuta: `dijkstra_with_steps()` y `shortest_path()`.
- Salida: animación de distancias y tabla final de la ruta.
- La tabla incluye latencia por enlace, latencia acumulada y ancho de banda del enlace.

### Pestaña 3 — Prim MST

- Entrada: no requiere entrada adicional; empieza desde el primer servidor del dataset.
- Ejecuta: `prim_mst()`.
- Salida: costo MST, costo total de todas las aristas, ahorro, tabla de aristas y gráfica de costo acumulado.
- La tabla muestra latencia, costo y `bandwidth_gbps`.

### Pestaña 4 — KD-tree

- Entrada: latitud y longitud del cliente desde la barra lateral.
- Ejecuta: búsqueda de vecino más cercano en KD-tree.
- Salida: centro de datos más cercano, distancia a cada servidor, mini mapa y visualización de particiones.
- El KD-tree usa solo nodos `server` porque la pregunta es a qué centro de datos debe conectarse un cliente nuevo.

### Pestaña 5 — HashMap

- Entrada: nombre de nodo en una caja de búsqueda.
- Ejecuta: `Graph.get_node_by_name()`, respaldado por el HashMap propio.
- Salida: resultado de búsqueda, tiempo medido en microsegundos, comparación contra búsqueda lineal y distribución de cubetas.

### Pestaña 6 — Complejidad

- Muestra complejidades de HashMap, Graph, Dijkstra, Prim y KD-tree.
- Incluye respuestas tipo profesor para defender decisiones de diseño.

### Pestaña 7 — Secuencia Temporal

- Entrada: slider de velocidad de animación.
- Ejecuta: `dijkstra_with_steps()` y `prim_with_steps()`.
- Salida: mapas animados que muestran la expansión de Dijkstra y el crecimiento del MST de Prim.

## Instalación y Ejecución

Crear y activar entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar pruebas:

```bash
pytest -q
```

Ejecutar dashboard:

```bash
streamlit run app.py
```

Ejecutar menú por consola:

```bash
python src/main.py
```

Ejecutar demo guiado:

```bash
python src/demo.py
python src/demo.py --lat 19.4326 --lon -99.1332
```

## Recrear o Rellenar los Datos

No hay base de datos externa. La "base de datos" del proyecto son los CSV en `data/`.

Para reseed:

1. Editar `data/nodes.csv` y `data/edges.csv`.
2. Mantener todas las columnas requeridas.
3. Verificar que cada `source` y `target` exista en `nodes.csv`.
4. Mantener `latency_ms`, `cost_usd` y `bandwidth_gbps` como valores no negativos.
5. Ejecutar `pytest -q`.
6. Ejecutar `streamlit run app.py` y revisar el dashboard.

## Supuestos y Limitaciones

- La red se modela como enlaces de fibra no dirigidos.
- Dijkstra optimiza solo latencia; el ancho de banda se muestra como metadato de capacidad.
- Prim optimiza solo costo; el ancho de banda se muestra para contexto.
- KD-tree usa solo servidores y poda con distancia euclidiana; al final reporta distancia Haversine en kilómetros.
- El dataset es pequeño para facilitar una presentación de clase; los beneficios de complejidad se vuelven más visibles con redes más grandes.
- Streamlit y Plotly se usan para presentación; los algoritmos centrales están implementados manualmente.
