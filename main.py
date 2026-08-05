import argparse
from src.parser import parse_recipes, parse_tags
from src.graph import build_graph, calculate_community_data
from src.exporter import export_interactive_html


def main():
    parser = argparse.ArgumentParser(description="Minecraft Crafting Map Network Analyzer")
    parser.add_argument('--recipes', type=str, required=True, help='Path to recipes folder')
    parser.add_argument('--tags', type=str, default='', help='Path to tags folder')
    parser.add_argument('--out', type=str, default='minecraft_map.html', help='Output HTML filename')

    args = parser.parse_args()

    print("Parsing recipe data...")
    recipe_edges = parse_recipes(args.recipes)

    tag_edges = []
    if args.tags:
        print("Parsing item tag definitions...")
        tag_edges = parse_tags(args.tags)

    print("Building NetworkX directed graph...")
    G = build_graph(recipe_edges, tag_edges)

    print(f"Graph constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    if G.number_of_nodes() == 0:
        print("Error: Graph contains no nodes. Check your recipe directory path.")
        return

    print("Calculating modularity clusters and out-degree centrality...")
    nodes_data, edges_data = calculate_community_data(G)

    print("Exporting visual HTML report...")
    export_interactive_html(nodes_data, edges_data, args.out)


if __name__ == '__main__':
    main()