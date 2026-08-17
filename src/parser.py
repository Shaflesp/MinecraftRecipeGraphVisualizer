import os
import json
import csv
from PIL import Image

FLATTENING_MAP = {}
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.normpath(os.path.join(script_dir, '..', 'translations.csv'))

if os.path.exists(csv_path):
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    FLATTENING_MAP[row[0].strip()] = row[1].strip()
    except Exception as e:
        print(f"[!] Warning: Could not read translations.csv: {e}")


def translate_legacy_item(item_name, data_val):
    if not item_name:
        return None
    if not item_name.startswith('minecraft:'):
        item_name = f"minecraft:{item_name}"

    # 1. Try exact metadata match (e.g., "minecraft:log:0" -> "oak_log")
    if data_val is not None and data_val != 32767:
        exact_key = f"{item_name}:{data_val}"
        if exact_key in FLATTENING_MAP:
            return FLATTENING_MAP[exact_key].replace('minecraft:', '')

    # 2. Try wildcard match from translations.csv (e.g., "minecraft:log:*" -> "#logs")
    wildcard_key = f"{item_name}:*"
    if wildcard_key in FLATTENING_MAP:
        return FLATTENING_MAP[wildcard_key].replace('minecraft:', '')

    # 3. Fallback for standard items with no special metadata rules (e.g., "minecraft:iron_ingot")
    return item_name.replace('minecraft:', '')


def extract_item(ingredient):
    if isinstance(ingredient, str): return ingredient.replace('minecraft:', '')
    if isinstance(ingredient, list):
        items = []
        for i in ingredient:
            extracted = extract_item(i)
            if isinstance(extracted, list):
                items.extend(extracted)
            elif extracted:
                items.append(extracted)
        return items
    if isinstance(ingredient, dict):
        if 'data' in ingredient and ('item' in ingredient or 'id' in ingredient):
            item_name = ingredient.get('item', ingredient.get('id', ''))
            return translate_legacy_item(item_name, ingredient['data'])
        if 'item' in ingredient:
            return ingredient['item'].replace('minecraft:', '')
        elif 'tag' in ingredient:
            return '#' + ingredient['tag'].replace('minecraft:', '')
        elif 'id' in ingredient:
            return ingredient['id'].replace('minecraft:', '')
    return None


def process_recipe_json(data, edges):
    recipe_type = data.get('type', '')
    if recipe_type not in ['minecraft:crafting_shaped', 'minecraft:crafting_shapeless', 'crafting_shaped',
                           'crafting_shapeless']:
        return

    result = data.get('result', {})
    if isinstance(result, str):
        result_item = result.replace('minecraft:', '')
    else:
        r_item = result.get('item', result.get('id', ''))
        r_data = result.get('data', 0)
        result_item = translate_legacy_item(r_item, r_data)

    if not result_item: return

    ingredients_list = []
    if 'shaped' in recipe_type:
        for key, ingredient in data.get('key', {}).items():
            extracted = extract_item(ingredient)
            if isinstance(extracted, list):
                ingredients_list.extend(extracted)
            elif extracted:
                ingredients_list.append(extracted)

    elif 'shapeless' in recipe_type:
        for ingredient in data.get('ingredients', []):
            extracted = extract_item(ingredient)
            if isinstance(extracted, list):
                ingredients_list.extend(extracted)
            elif extracted:
                ingredients_list.append(extracted)

    for ing in set(ingredients_list):
        if ing: edges.append((ing, result_item))


def parse_recipes_from_dump(dump_dir):
    edges = []
    for root, dirs, files in os.walk(dump_dir):
        if 'recipes' in root or 'recipe' in root:
            for file in files:
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            process_recipe_json(data, edges)
                    except Exception:
                        pass
    return edges


def parse_tags_from_dump(dump_dir):
    tag_edges = []
    for root, dirs, files in os.walk(dump_dir):
        if 'tags' in root and ('items' in root or 'item' in root):
            for file in files:
                if file.endswith('.json'):
                    parts = root.replace('\\', '/').split('/')
                    try:
                        idx = parts.index('item')
                    except ValueError:
                        try:
                            idx = parts.index('items')
                        except ValueError:
                            continue

                    rel_path = '/'.join(parts[idx + 1:])

                    # BUGFIX: Prevent the extra slash from breaking tag strings!
                    if rel_path:
                        tag_name = f"#{rel_path}/{file}".replace('.json', '')
                    else:
                        tag_name = f"#{file}".replace('.json', '')

                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for value in data.get('values', []):
                                if isinstance(value, str):
                                    tag_edges.append((value.replace('minecraft:', ''), tag_name))
                                elif isinstance(value, dict) and 'id' in value:
                                    tag_edges.append((value['id'].replace('minecraft:', ''), tag_name))
                    except Exception:
                        pass
    return tag_edges


def process_textures_from_dump(dump_dir, output_dir="icons"):
    os.makedirs(output_dir, exist_ok=True)
    extracted_count = 0
    for root, dirs, files in os.walk(dump_dir):
        norm_root = root.replace('\\', '/')

        # 'textures/item' matches 'textures/items' automatically via substring
        if 'textures/item' in norm_root or 'textures/block' in norm_root:
            for file in files:
                if file.endswith('.png'):
                    try:
                        img_path = os.path.join(root, file)
                        parts = norm_root.split('/')
                        idx = parts.index('textures')
                        rel_dir = '/'.join(parts[idx+1:])

                        # --- Normalize old paths to modern format ---
                        if rel_dir.startswith('items'):
                            rel_dir = rel_dir.replace('items', 'item', 1)
                        elif rel_dir.startswith('blocks'):
                            rel_dir = rel_dir.replace('blocks', 'block', 1)

                        out_path = os.path.join(output_dir, rel_dir, file)
                        os.makedirs(os.path.dirname(out_path), exist_ok=True)

                        with Image.open(img_path) as img:
                            width, height = img.size
                            if height > width: img = img.crop((0, 0, width, width))
                            img.save(out_path)
                        extracted_count += 1
                    except Exception:
                        pass
    return True