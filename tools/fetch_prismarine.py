import os
import json
import urllib.request
import sys


def fetch_prismarine(version):
    base_url = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data"

    print(f"[*] Querying PrismarineJS database for version {version}...")

    # 1. Fetch the data paths to find where this version lives in their repo
    try:
        req = urllib.request.urlopen(f"{base_url}/dataPaths.json")
        paths = json.loads(req.read().decode('utf-8'))
    except Exception as e:
        print(f"[!] Failed to reach Prismarine GitHub: {e}")
        return

    # Prismarine maps some versions together (e.g. 1.14.4 -> 1.14)
    # We check if the exact version exists, or fallback to the closest match
    if "pc" not in paths: return

    version_key = version
    if version_key not in paths["pc"]:
        print(f"[!] Version {version} not directly mapped. Checking aliases...")
        fallback = '.'.join(version.split('.')[:2])
        if fallback in paths["pc"]:
            version_key = fallback
            print(f"[*] Found fallback version: {version_key}")
        else:
            print(f"[!] Version {version} not found in Prismarine data.")
            return

    recipes_folder = paths["pc"][version_key].get("recipes")
    items_folder = paths["pc"][version_key].get("items")

    if not recipes_folder or not items_folder:
        print(f"[!] Missing recipe or item mappings for {version}.")
        return

    # 2. Fetch Items
    print("[*] Downloading items.json map...")
    req = urllib.request.urlopen(f"{base_url}/{items_folder}/items.json")
    items_data = json.loads(req.read().decode('utf-8'))

    item_map = {}
    for item in items_data:
        item_map[item['id']] = item['name']

    # 3. Fetch Recipes
    print("[*] Downloading recipes.json...")
    req = urllib.request.urlopen(f"{base_url}/{recipes_folder}/recipes.json")
    recipes_data = json.loads(req.read().decode('utf-8'))

    # 4. Create the standardized dump folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dump_dir = os.path.join(script_dir, "..", "dumps", version, "data", "minecraft", "recipes")

    dump_dir = os.path.normpath(dump_dir)
    os.makedirs(dump_dir, exist_ok=True)

    # 5. Translate Prismarine format to Standard Vanilla JSON format
    print(f"[*] Translating recipes and preserving metadata for /dumps/{version}/...")
    recipe_count = 0

    for result_id_str, recipe_list in recipes_data.items():
        result_id = int(result_id_str)
        result_name = item_map.get(result_id, f"unknown_{result_id}")

        for i, recipe in enumerate(recipe_list):

            result_meta = 0
            if "result" in recipe and isinstance(recipe["result"], dict):
                result_meta = recipe["result"].get("metadata", 0)

            vanilla_json = {
                "type": "minecraft:crafting_shapeless",
                "result": {
                    "item": f"minecraft:{result_name}",
                    "data": result_meta
                },
                "ingredients": []
            }

            def add_ingredient(cell):
                if cell is None: return

                cell_id = None
                cell_meta = 0

                if isinstance(cell, int):
                    cell_id = cell
                elif isinstance(cell, dict):
                    cell_id = cell.get("id")
                    cell_meta = cell.get("metadata", 0)

                if cell_id is not None:
                    ing_name = item_map.get(cell_id, "unknown")
                    vanilla_json["ingredients"].append({
                        "item": f"minecraft:{ing_name}",
                        "data": cell_meta
                    })

            if "inShape" in recipe:
                for row in recipe["inShape"]:
                    for cell in row:
                        add_ingredient(cell)

            elif "ingredients" in recipe:
                for cell in recipe["ingredients"]:
                    add_ingredient(cell)

            if vanilla_json["ingredients"]:
                file_path = os.path.join(dump_dir, f"{result_name}_meta{result_meta}_{i}.json")
                with open(file_path, "w", encoding='utf-8') as f:
                    json.dump(vanilla_json, f, indent=4)
                recipe_count += 1

    print(f"✅ Successfully extracted and translated {recipe_count} recipes for {version}!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_prismarine.py <version>")
        print("Example: python fetch_prismarine.py 1.12.2")
    else:
        fetch_prismarine(sys.argv[1])