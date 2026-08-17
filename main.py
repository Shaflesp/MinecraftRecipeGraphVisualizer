import argparse
import os
import re
from src.parser import parse_recipes_from_dump, parse_tags_from_dump, process_textures_from_dump
from src.graph import build_graph, calculate_community_data, calculate_graph_metrics
from src.exporter import export_interactive_html
from src.database import save_version_data, load_version_data


def run_parser(version, dump_dir, db_path):
    """Core logic to crunch the data from a dump folder and save to SQLite."""
    if not os.path.exists(dump_dir):
        print(f"[!] Error: Dump directory not found at {dump_dir}")
        return False

    print(f"Analyzing {version} from {dump_dir}...")
    use_icons = process_textures_from_dump(dump_dir)

    print("Parsing recipes and tags...")
    recipe_edges = parse_recipes_from_dump(dump_dir)
    tag_edges = parse_tags_from_dump(dump_dir)

    print("Building Graph & computing math...")
    G = build_graph(recipe_edges, tag_edges)

    if G.number_of_nodes() == 0:
        print("[!] Error: Graph contains no nodes. Aborting.")
        return False

    nodes_data, edges_data = calculate_community_data(G, use_icons=use_icons)
    metrics_data = calculate_graph_metrics(G)

    print("Saving to SQLite...")
    save_version_data(db_path, version, nodes_data, edges_data, metrics_data)
    print(f"✅ Version '{version}' successfully stored in {db_path}\n")
    return True


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


def get_version_tuple(version_str):
    """Converts '1.12.2' or '1.8-pre' into numeric tuples like (1, 12, 2) for accurate sorting."""
    return tuple(int(n) for n in re.findall(r'\d+', version_str))


def main():
    parser = argparse.ArgumentParser(description="Minecraft Crafting Database Analyzer")
    parser.add_argument('--db', type=str, default='minecraft_data.db', help='SQLite database file')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # 1. Single Parse Command
    parse_cmd = subparsers.add_parser('parse', help='Parse a single dump folder and save its graph to SQLite')
    parse_cmd.add_argument('version', type=str, help='Name of the version (e.g., "1.20.4")')
    parse_cmd.add_argument('dump_dir', type=str, help='Path to the Minecraft dump folder')

    # 2. Batch Parse-All Command
    parse_all_cmd = subparsers.add_parser('parse-all',
                                          help='Crawl a root dumps directory and parse all versions chronologically')
    parse_all_cmd.add_argument('dumps_root', type=str, help='Path to the root dumps folder (e.g., "dumps/")')

    # 3. Render Command
    render_cmd = subparsers.add_parser('render', help='Render an interactive HTML map from SQLite data')
    render_cmd.add_argument('version', type=str, help='Name of the version to render')
    render_cmd.add_argument('--out', type=str, default='minecraft_map.html', help='Output HTML filename')

    args = parser.parse_args()

    if args.command == 'parse':
        run_parser(args.version, args.dump_dir, args.db)

    elif args.command == 'parse-all':
        if not os.path.exists(args.dumps_root):
            print(f"Error: Root directory '{args.dumps_root}' not found.")
            return

        subdirs = [d for d in os.listdir(args.dumps_root) if os.path.isdir(os.path.join(args.dumps_root, d))]

        subdirs.sort(key=get_version_tuple)

        print(f"Found {len(subdirs)} versions to parse: {subdirs}\n")

        for version in subdirs:
            dump_dir = os.path.join(args.dumps_root, version)
            print(f"{'=' * 40}")
            print(f" Batch Processing: {version} ")
            print(f"{'=' * 40}")
            try:
                run_parser(version, dump_dir, args.db)
            except Exception as e:
                print(f"[!] Critical failure processing {version}: {e}\n")

    elif args.command == 'render':
        run_renderer(args)


if __name__ == '__main__':
    main()