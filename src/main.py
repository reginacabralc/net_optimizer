"""
main.py — Modo interactivo de NetOptimizer.

Permite al usuario ingresar coordenadas, elegir nodos fuente/destino
y ejecutar cada algoritmo de forma independiente.

Uso: python src/main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_graph
from src.dijkstra import shortest_path
from src.kdtree import KDTree
from src.prim import prim_mst, mst_summary
from src.visualize import plot_network


def print_menu() -> None:
    print("\n" + "═" * 50)
    print("  NetOptimizer — Menú Principal")
    print("═" * 50)
    print("  1. Mostrar red completa")
    print("  2. Buscar nodo por nombre (HashMap)")
    print("  3. Servidor más cercano (KD-tree)")
    print("  4. Ruta de menor latencia (Dijkstra)")
    print("  5. Red de fibra mínima (Prim MST)")
    print("  6. Demo completo + visualización")
    print("  0. Salir")
    print("─" * 50)


def list_nodes(graph, node_type: str = None) -> None:
    nodes = graph.get_all_nodes() if node_type is None else graph.get_nodes_by_type(node_type)
    for n in nodes:
        print(f"  [{n.node_id:4s}] {n.name:30s} ({n.node_type})")


def main() -> None:
    print("\nCargando red ISP...")
    graph = load_graph(verbose=False)
    print(f"Red cargada: {graph}")

    while True:
        print_menu()
        choice = input("  Opción: ").strip()

        if choice == "0":
            print("  Hasta luego.\n")
            break

        elif choice == "1":
            print(f"\n{graph.summary()}\n")
            print("  Todos los nodos:")
            list_nodes(graph)

        elif choice == "2":
            name = input("  Nombre del nodo: ").strip()
            try:
                node = graph.get_node_by_name(name)
                print(f"\n  Encontrado: {node}")
            except KeyError:
                print(f"\n  Nodo '{name}' no encontrado.")
                print("  Nodos disponibles:")
                for n in graph.get_all_nodes():
                    print(f"    {n.name}")

        elif choice == "3":
            try:
                lat = float(input("  Latitud del cliente: "))
                lon = float(input("  Longitud del cliente: "))
            except ValueError:
                print("  Coordenadas inválidas.")
                continue

            servers = graph.get_nodes_by_type("server")
            tree = KDTree()
            tree.build(servers)
            nearest, dist_km = tree.nearest_neighbor(lat, lon)
            print(f"\n  Servidor más cercano: {nearest.name}")
            print(f"  Distancia: {dist_km:.3f} km")

        elif choice == "4":
            print("\n  Nodos disponibles:")
            list_nodes(graph)
            src = input("  ID nodo origen: ").strip()
            tgt = input("  ID nodo destino: ").strip()

            try:
                latency, path = shortest_path(graph, src, tgt)
                if path:
                    names = [graph.get_node(n).name for n in path]
                    print(f"\n  Ruta: {' → '.join(names)}")
                    print(f"  Latencia total: {latency:.1f} ms")
                else:
                    print("  No existe ruta entre esos nodos.")
            except KeyError as e:
                print(f"  Error: {e}")

        elif choice == "5":
            mst_edges, total_cost = prim_mst(graph, start_id="S01")
            print(f"\n{mst_summary(mst_edges, graph)}")

        elif choice == "6":
            try:
                lat = float(input("  Latitud del nuevo cliente [19.4326]: ").strip() or "19.4326")
                lon = float(input("  Longitud del nuevo cliente [-99.1332]: ").strip() or "-99.1332")
            except ValueError:
                lat, lon = 19.4326, -99.1332

            servers = graph.get_nodes_by_type("server")
            tree = KDTree()
            tree.build(servers)
            nearest, dist_km = tree.nearest_neighbor(lat, lon)

            users = graph.get_nodes_by_type("user")
            from src.kdtree import _haversine_dist
            src_node = min(users, key=lambda u: _haversine_dist(lat, lon, u.lat, u.lon))

            latency, path = shortest_path(graph, src_node.node_id, nearest.node_id)
            mst_edges, total_cost = prim_mst(graph, start_id="S01")

            plot_network(
                graph=graph,
                mst_edges=mst_edges,
                dijkstra_path=path if path else None,
                nearest_server=nearest,
                new_client=(lat, lon),
                title=f"NetOptimizer | Dijkstra: {latency:.0f}ms | Prim MST: ${total_cost:,.0f} | KD-tree: {nearest.name}",
                show=True,
            )
        else:
            print("  Opción no válida.")


if __name__ == "__main__":
    main()
