import os
import json


def extract_item(ingredient):
    if isinstance(ingredient, str):
        return ingredient.replace('minecraft:', '')
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
        if 'item' in ingredient:
            return ingredient['item'].replace('minecraft:', '')
        elif 'tag' in ingredient:
            return '#' + ingredient['tag'].replace('minecraft:', '')
        elif 'id' in ingredient:
            return ingredient['id'].replace('minecraft:', '')
    return None


def parse_recipes(recipes_dir):
    edges = []
    if not os.path.exists(recipes_dir):
        return edges

    for filename in os.listdir(recipes_dir):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(recipes_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            recipe_type = data.get('type', '')
            if recipe_type not in ['minecraft:crafting_shaped', 'minecraft:crafting_shapeless']:
                continue

            result = data.get('result', {})
            if isinstance(result, str):
                result_item = result.replace('minecraft:', '')
            else:
                result_item = result.get('item', result.get('id', '')).replace('minecraft:', '')

            if not result_item:
                continue

            ingredients_list = []
            if recipe_type == 'minecraft:crafting_shaped':
                for key, ingredient in data.get('key', {}).items():
                    extracted = extract_item(ingredient)
                    if isinstance(extracted, list):
                        ingredients_list.extend(extracted)
                    elif extracted:
                        ingredients_list.append(extracted)

            elif recipe_type == 'minecraft:crafting_shapeless':
                for ingredient in data.get('ingredients', []):
                    extracted = extract_item(ingredient)
                    if isinstance(extracted, list):
                        ingredients_list.extend(extracted)
                    elif extracted:
                        ingredients_list.append(extracted)

            for ing in set(ingredients_list):
                if ing:
                    edges.append((ing, result_item))
        except Exception:
            pass
    return edges


def parse_tags(tags_dir):
    tag_edges = []
    if not os.path.exists(tags_dir):
        return tag_edges

    # STRICT FILTER: Only parse item tags to prevent graph pollution (#game_events, etc.)
    item_tags_dir = None
    if os.path.basename(tags_dir) in ['item', 'items']:
        item_tags_dir = tags_dir
    else:
        for subdir in ['items', 'item']:
            potential_path = os.path.join(tags_dir, subdir)
            if os.path.exists(potential_path):
                item_tags_dir = potential_path
                break

    if not item_tags_dir:
        print(f"Warning: Could not find 'item' or 'items' folder in {tags_dir}. Skipping tags.")
        return tag_edges

    for root, _, files in os.walk(item_tags_dir):
        for filename in files:
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(root, filename)

            # Create tag names relative to the item directory so they match recipe strings
            rel_path = os.path.relpath(filepath, item_tags_dir)
            tag_name = '#' + rel_path.replace('\\', '/').replace('.json', '')

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for value in data.get('values', []):
                    if isinstance(value, str):
                        child = value.replace('minecraft:', '')
                        tag_edges.append((child, tag_name))
                    elif isinstance(value, dict) and 'id' in value:
                        child = value['id'].replace('minecraft:', '')
                        tag_edges.append((child, tag_name))
            except Exception:
                pass

    return tag_edges