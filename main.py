import argparse
import os
from src.parser import parse_recipes_from_jar, parse_tags_from_jar, extract_textures_from_jar
from src.graph import build_graph, calculate_community_data, calculate_graph_metrics
from src.exporter import export_interactive_html


def main():
    parser = argparse.ArgumentParser(description="Minecraft Crafting Map Network Analyzer")
    # Make the JAR file the primary required argument
    parser.add_argument('jar', type=str, help='Path to the Minecraft client .jar file')
    parser.add_argument('--out', type=str, default='minecraft_map.html', help='Output HTML filename')

    args = parser.parse_args()

    if not os.path.exists(args.jar):
        print(f"Error: JAR file not found at {args.jar}")
        return

    print(f"Analyzing {os.path.basename(args.jar)}...")

    # 1. Extract icons to local disk
    use_icons = extract_textures_from_jar(args.jar)

    # 2. Parse data directly from memory
    print("Parsing recipe data from archive...")
    recipe_edges = parse_recipes_from_jar(args.jar)

    print("Parsing item tags from archive...")
    tag_edges = parse_tags_from_jar(args.jar)

    # 3. Build Graph
    print("Building NetworkX directed graph...")
    G = build_graph(recipe_edges, tag_edges)
    print(f"Graph constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    if G.number_of_nodes() == 0:
        print("Error: Graph contains no nodes. Are you sure this is a standard Minecraft client jar?")
        return

    # 4. Math & Export
    print("Calculating modularity clusters and applying visuals...")
    nodes_data, edges_data = calculate_community_data(G, use_icons=use_icons)

    # 5. Calculating metrics
    print("Crunching network metrics...")
    metrics_data = calculate_graph_metrics(G)

    print("Exporting visual HTML report...")
    export_interactive_html(nodes_data, edges_data, metrics_data=metrics_data, output_file=args.out)


if __name__ == '__main__':
    main()