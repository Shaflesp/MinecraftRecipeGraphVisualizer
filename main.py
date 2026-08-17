import argparse
import os
from src.parser import parse_recipes_from_dump, parse_tags_from_dump, process_textures_from_dump
from src.graph import build_graph, calculate_community_data, calculate_graph_metrics
from src.exporter import export_interactive_html
from src.database import save_version_data, load_version_data


def run_parser(args):
    """Phase 1: Crunch the data from a dump folder and save to SQLite."""

    dump_dir = args.dump_dir

    if not os.path.exists(dump_dir):
        print(f"Error: Dump directory not found at {dump_dir}")
        return

    print(f"Analyzing {args.version} from {dump_dir}...")
    use_icons = process_textures_from_dump(dump_dir)

    print("Parsing recipes and tags...")
    recipe_edges = parse_recipes_from_dump(dump_dir)
    tag_edges = parse_tags_from_dump(dump_dir)

    print("Building Graph & computing math...")
    G = build_graph(recipe_edges, tag_edges)

    if G.number_of_nodes() == 0:
        print("Error: Graph contains no nodes. Aborting.")
        return

    nodes_data, edges_data = calculate_community_data(G, use_icons=use_icons)
    metrics_data = calculate_graph_metrics(G)

    print("Saving to SQLite...")
    save_version_data(args.db, args.version, nodes_data, edges_data, metrics_data)
    print(f"✅ Version '{args.version}' successfully stored in {args.db}")


def run_renderer(args):
    """Phase 2: Pull from SQLite and generate HTML."""
    print(f"Fetching '{args.version}' from database...")
    nodes_data, edges_data, metrics_data = load_version_data(args.db, args.version)

    if not nodes_data:
        print(f"Error: No data found for version '{args.version}' in {args.db}.")
        print("Did you run the 'parse' command first?")
        return

    print("Generating HTML map...")
    export_interactive_html(nodes_data, edges_data, metrics_data=metrics_data, output_file=args.out)


def main():
    parser = argparse.ArgumentParser(description="Minecraft Crafting Database Analyzer")
    parser.add_argument('--db', type=str, default='minecraft_data.db', help='SQLite database file')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # The 'parse' command
    parse_cmd = subparsers.add_parser('parse', help='Parse a dump folder and save its graph to SQLite')
    parse_cmd.add_argument('version', type=str, help='Name of the version (e.g., "1.20.4")')
    parse_cmd.add_argument('dump_dir', type=str, help='Path to the Minecraft dump folder')

    # The 'render' command
    render_cmd = subparsers.add_parser('render', help='Render an interactive HTML map from SQLite data')
    render_cmd.add_argument('version', type=str, help='Name of the version to render')
    render_cmd.add_argument('--out', type=str, default='minecraft_map.html', help='Output HTML filename')

    args = parser.parse_args()

    if args.command == 'parse':
        run_parser(args)
    elif args.command == 'render':
        run_renderer(args)


if __name__ == '__main__':
    main()