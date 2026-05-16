# NetOptimizer — Internet / Telecom Network

NetOptimizer is a data structures project for **Variant 4: Internet / Telecom Network**. It models a small fiber-optic ISP network in Mexico City and demonstrates how classic structures and algorithms solve practical telecom optimization questions:

- What is the **minimum-latency route** from a user area to a datacenter?
- What is the **minimum-cost fiber backbone** that connects all network nodes?
- Which datacenter is **geographically nearest** to a new client?
- How can an extra course data structure improve lookup performance?

The project includes algorithm modules, CSV data, unit tests, a CLI demo, Matplotlib visualization, and a Streamlit dashboard.

## Variant 4 Requirements

| Requirement | Project implementation | Main files |
|---|---|---|
| Dijkstra for minimum-latency route | Uses `latency_ms` as the edge weight and returns the lowest total latency path. | `src/dijkstra.py`, `src/graph.py` |
| Prim for minimum-cost fiber network | Uses `cost_usd` as the edge weight and returns the minimum spanning tree. | `src/prim.py`, `src/graph.py` |
| KD-tree for nearest server | Builds a 2D KD-tree from server/datacenter coordinates and finds the nearest server to a client coordinate. | `src/kdtree.py` |
| Additional course data structure | Implements a custom `HashMap` with separate chaining and uses it inside `Graph` for node and name indexes. | `src/hash_map.py`, `src/graph.py` |
| Comparative complexity analysis | Included in module docs, tests, dashboard, and this README. | `README.md`, `app.py` |

## Data Model

Data is stored in CSV files under `data/`.

### `data/nodes.csv`

| Column | Meaning |
|---|---|
| `node_id` | Unique node identifier. |
| `node_type` | One of `server`, `router`, `switch`, or `user`. |
| `name` | Human-readable network location name. |
| `lat` | Latitude in decimal degrees. |
| `lon` | Longitude in decimal degrees. |

### `data/edges.csv`

| Column | Meaning |
|---|---|
| `source` | Origin node id. |
| `target` | Destination node id. |
| `latency_ms` | Link latency in milliseconds. This is Dijkstra's optimization criterion. |
| `cost_usd` | Fiber installation or network cost. This is Prim's optimization criterion. |
| `bandwidth_gbps` | Link capacity in gigabits per second. This is telecom metadata displayed in edge/path details, but it does not replace latency or cost as the required algorithm weights. |

The graph is undirected: every CSV edge is inserted in both directions in the adjacency list.

## Algorithms and Structures

### Dijkstra — Minimum Latency

`src/dijkstra.py` implements Dijkstra with `heapq` as a min-priority queue.

- Input: graph, source node, optional target node.
- Weight used: `latency_ms`.
- Output: total minimum latency and route.
- Why Dijkstra: BFS minimizes hop count, not latency. Bellman-Ford supports negative weights but is slower; telecom latencies are non-negative.

Complexity:

- Time: `O((V + E) log V)` with a min-heap.
- Space: `O(V)` for distances, predecessors, heap state, and visited nodes.

### Prim — Minimum-Cost Fiber Network

`src/prim.py` implements Prim with a min-heap.

- Input: graph and optional starting node.
- Weight used: `cost_usd`.
- Output: MST edges and total cost.
- Why Prim: it grows a connected fiber backbone by repeatedly choosing the cheapest edge that reaches a new node. It is natural for an ISP network expansion story.

Complexity:

- Time: `O(E log V)`.
- Space: `O(V + E)`.

### KD-tree — Nearest Datacenter

`src/kdtree.py` implements a 2D KD-tree over `(lat, lon)` coordinates for server nodes only.

- Input: datacenter/server nodes.
- Query: new client latitude and longitude.
- Output: nearest server and distance in kilometers.
- Why KD-tree: linear search checks every server: `O(n)`. KD-tree partitions the plane and gives average `O(log n)` nearest-neighbor search.

Complexity:

- Build: `O(n log n)`.
- Nearest search: `O(log n)` average, `O(n)` worst case.
- Space: `O(n)`.

### HashMap — Additional Course Data Structure

`src/hash_map.py` implements a custom hash table with:

- Polynomial string hash.
- Separate chaining for collisions.
- Automatic rehashing at load factor `0.75`.

The graph uses this HashMap for:

- `node_id -> Node` lookup.
- `node_id -> adjacency list` lookup.
- `name -> node_id` lookup.

Why HashMap was chosen:

| Operation | HashMap average | Linear list |
|---|---:|---:|
| Insert | `O(1)` amortized | `O(1)` |
| Search by id/name | `O(1)` average | `O(n)` |
| Delete | `O(1)` average | `O(n)` |
| Worst-case search | `O(n)` | `O(n)` |

The dashboard includes a live lookup and benchmark to justify this choice.

## Backend Flow

1. `src/data_loader.py` reads `nodes.csv` and `edges.csv`.
2. It validates required columns, including `bandwidth_gbps`.
3. It creates immutable `Node` and `Edge` dataclasses from `src/models.py`.
4. It inserts them into `Graph` from `src/graph.py`.
5. `Graph` stores nodes and adjacency lists in the custom `HashMap`.
6. Algorithms consume the graph through `get_neighbors()`, `get_all_nodes()`, and typed node filters.

Important graph operations:

| Operation | Complexity | Notes |
|---|---:|---|
| `add_node` | `O(1)` average | HashMap insert. |
| `add_edge` | `O(1)` average | Adds two adjacency entries for undirected graph. |
| `get_node` | `O(1)` average | HashMap lookup. |
| `get_node_by_name` | `O(1)` average | Uses name index HashMap. |
| `get_neighbors` | `O(1)` average | Returns adjacency list reference. |
| `get_all_edges` | `O(V + E)` | Scans adjacency lists and removes duplicates. |

## Dashboard Guide

Run it with:

```bash
streamlit run app.py
```

The dashboard loads the graph once with Streamlit caching, builds the KD-tree from server nodes, computes Dijkstra and Prim results from the selected inputs, and renders all views with Plotly.

### Sidebar

- Input: new client `Latitud` and `Longitud`.
- Input: checkboxes for showing MST, Dijkstra route, and nearest server on the main map.
- Input: Dijkstra source node selector.
- Backend triggered: graph loading, KD-tree nearest search, Dijkstra route, Prim MST.

### Tab 1 — Red ISP

- Shows the full network map.
- Displays base edges, nodes by type, the selected Dijkstra path, Prim MST, nearest server, and new client coordinate.
- Edge hover details include latency, cost, and `bandwidth_gbps`.
- Demonstrates how all algorithms relate to the same graph.

### Tab 2 — Dijkstra paso a paso

- Input: source node from the sidebar; target is the nearest datacenter from KD-tree.
- Triggers: `dijkstra_with_steps()` and `shortest_path()`.
- Output: animated distance chart plus final route table.
- Route table includes step latency, accumulated latency, and link bandwidth.

### Tab 3 — Prim MST

- Input: no extra user input; starts from the first server in the dataset.
- Triggers: `prim_mst()`.
- Output: MST total cost, total cost of all edges, savings, MST edge table, and cumulative cost chart.
- MST table displays latency, cost, and `bandwidth_gbps`.

### Tab 4 — KD-tree

- Input: client latitude and longitude from the sidebar.
- Triggers: KD-tree nearest-neighbor search.
- Output: nearest datacenter, distance to every server, mini-map, and KD-tree partition visualization.
- The KD-tree intentionally uses only `server` nodes because the question is where a new client should connect as an access/datacenter endpoint.

### Tab 5 — HashMap

- Input: node name search box.
- Triggers: `Graph.get_node_by_name()`, backed by the custom HashMap.
- Output: lookup result, measured microsecond timing, benchmark chart versus linear search, and bucket distribution.

### Tab 6 — Complejidad

- Shows complexity table for HashMap, Graph, Dijkstra, Prim, and KD-tree.
- Includes professor-style FAQ answers.

### Tab 7 — Timelapse

- Input: animation speed slider.
- Triggers: `dijkstra_with_steps()` and `prim_with_steps()`.
- Output: animated map showing Dijkstra expansion and Prim MST growth over the geographic network.

## Install and Run

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest -q
```

Run the dashboard:

```bash
streamlit run app.py
```

Run the CLI menu:

```bash
python src/main.py
```

Run the scripted demo:

```bash
python src/demo.py
python src/demo.py --lat 19.4326 --lon -99.1332
```

## Recreating or Reseeding Data

There is no external database. The "database" for this project is the CSV data in `data/`.

To reseed:

1. Edit `data/nodes.csv` and `data/edges.csv`.
2. Keep all required columns.
3. Ensure every edge `source` and `target` exists in `nodes.csv`.
4. Keep `latency_ms`, `cost_usd`, and `bandwidth_gbps` non-negative.
5. Run `pytest -q`.
6. Run `streamlit run app.py` and verify the dashboard.

## Assumptions and Limitations

- The network is modeled as undirected fiber links.
- Dijkstra optimizes latency only; bandwidth is displayed as capacity metadata.
- Prim optimizes cost only; bandwidth is displayed for context.
- KD-tree uses server nodes only and Euclidean pruning internally, then reports final Haversine distance in kilometers.
- The dataset is intentionally small for a class presentation; complexity benefits become more visible with larger networks.
- Streamlit and Plotly are used only for presentation; core algorithms are implemented manually.

## Suggested Future Improvements

| Improvement | Why it helps | Files/area | Difficulty |
|---|---|---|---|
| Add constrained routing, such as minimum latency with required minimum bandwidth. | Makes `bandwidth_gbps` operational, not only descriptive. | `src/dijkstra.py`, `app.py`, tests | Medium |
| Add import validation report for disconnected graphs and invalid edge endpoints. | Improves data quality and presentation confidence. | `src/data_loader.py`, `tests/` | Low |
| Add a larger synthetic network generator. | Makes complexity demos more convincing at scale. | `data/`, new seed script, dashboard benchmark | Medium |
| Add Haversine-aware KD-tree comparison mode. | Lets the project discuss approximation vs geographic accuracy. | `src/kdtree.py`, `app.py` | Medium |
| Add export buttons for MST and Dijkstra results. | Useful for reports and live demos. | `app.py` | Low |

## 10-Minute Live Presentation Plan

1. **0:00-0:45 — Problem.** Explain the ISP goals: latency, fiber cost, nearest datacenter.
2. **0:45-1:30 — Data.** Show nodes and edges, especially `latency_ms`, `cost_usd`, and `bandwidth_gbps`.
3. **1:30-2:30 — Graph and HashMap.** Explain adjacency list and custom HashMap lookup.
4. **2:30-4:00 — KD-tree.** Move the client coordinates and show nearest server and partitions.
5. **4:00-5:45 — Dijkstra.** Select a user/source, show the route and latency table.
6. **5:45-7:15 — Prim.** Show MST cost savings and edge table.
7. **7:15-8:15 — Timelapse.** Play Dijkstra and Prim animations.
8. **8:15-9:15 — Complexity.** Use the table and HashMap benchmark.
9. **9:15-10:00 — Wrap-up.** State how every Variant 4 requirement is satisfied and mention future work.

## Current Compliance Summary

- Dijkstra: compliant; uses `latency_ms`.
- Prim: compliant; uses `cost_usd`.
- KD-tree: compliant; supports nearest-server geospatial search.
- Additional data structure: compliant; custom HashMap is implemented and used by `Graph`.
- Telecom coherence: compliant; nodes, fiber links, latency, cost, bandwidth, routes, MST, and nearest datacenter all describe one ISP optimization system.
