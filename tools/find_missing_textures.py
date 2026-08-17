import os
import sys
import sqlite3

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.database import load_version_data

def generate_missing_report(db_path="minecraft_data.db", output_file="missing_textures_report.txt"):
    if not os.path.exists(db_path):
        print(f"[!] Database '{db_path}' not found.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT version_name FROM versions ORDER BY id ASC")
    versions = [r[0] for r in c.fetchall()]
    conn.close()

    total_missing = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Minecraft Recipe Graph - Missing Textures Report\n")
        f.write("================================================\n\n")

        for version in versions:
            nodes, edges, metrics = load_version_data(db_path, version)

            missing_items = []
            for node in nodes:
                node_id = node.get("id", "")

                # Skip tags (like #planks) because they never have textures
                if node_id.startswith('#'):
                    continue

                # If the node doesn't have an 'image' key, the texture failed to load
                if "image" not in node or not node.get("image"):
                    missing_items.append(node_id)

            missing_items.sort()
            total_missing += len(missing_items)

            # Output to console
            if missing_items:
                print(f"[*] {version}: Missing {len(missing_items)} textures.")
            else:
                print(f"[+] {version}: Perfect! 0 missing textures.")

            # Write details to the text file
            f.write(f"=== Version: {version} (Missing: {len(missing_items)}) ===\n")
            if missing_items:
                for i in range(0, len(missing_items), 5):
                    f.write(", ".join(missing_items[i:i + 5]) + "\n")
            else:
                f.write("All items perfectly textured!\n")
            f.write("\n")

    print(f"\n✅ Report generated! Total missing across all versions: {total_missing}")
    print(f"📄 Open '{output_file}' to see exactly what you need to look for.")


if __name__ == '__main__':
    generate_missing_report()