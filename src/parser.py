import json
import os
import zipfile


def extract_item(ingredient):
    """Parses ingredient objects across different Minecraft version formats."""
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


def parse_recipes_from_jar(jar_path):
    """Reads crafting recipes directly from the .jar archive in memory."""
    edges = []
    import json
    import zipfile

    with zipfile.ZipFile(jar_path, 'r') as jar:
        for file in jar.namelist():
            # Mojang renamed 'recipes/' to 'recipe/' in 1.21. We check for both!
            if (file.startswith('data/minecraft/recipes/') or
                file.startswith('data/minecraft/recipe/')) and file.endswith('.json'):

                try:
                    data = json.loads(jar.read(file).decode('utf-8'))

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


def parse_tags_from_jar(jar_path):
    """Reads item tags directly from the .jar archive in memory."""
    tag_edges = []
    with zipfile.ZipFile(jar_path, 'r') as jar:
        for file in jar.namelist():
            # Target both 'item' and 'items' tags to cover version differences
            if (file.startswith('data/minecraft/tags/items/') or
                file.startswith('data/minecraft/tags/item/')) and file.endswith('.json'):

                # Dynamically construct the tag name (e.g., #minecraft:logs)
                parts = file.split('/')
                try:
                    idx = parts.index('item')
                except ValueError:
                    idx = parts.index('items')

                rel_path = '/'.join(parts[idx + 1:])
                tag_name = '#' + rel_path.replace('.json', '')

                try:
                    data = json.loads(jar.read(file).decode('utf-8'))
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


def extract_textures_from_jar(jar_path, output_dir="icons"):
    """Extracts block and item textures to a local folder for HTML rendering."""
    print(f"Extracting textures from {os.path.basename(jar_path)}...")
    os.makedirs(output_dir, exist_ok=True)

    extracted_count = 0
    with zipfile.ZipFile(jar_path, 'r') as jar:
        for file in jar.namelist():
            if file.startswith('assets/minecraft/textures/item/') or \
                    file.startswith('assets/minecraft/textures/block/'):
                if file.endswith('.png'):
                    jar.extract(file, output_dir)
                    extracted_count += 1

    print(f"Extracted {extracted_count} textures to /{output_dir}/")
    return True