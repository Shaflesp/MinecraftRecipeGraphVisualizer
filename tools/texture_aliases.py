import os
import sys
import zipfile
import json
import csv


def extract_texture_name(texture_path):
    if ':' in texture_path:
        texture_path = texture_path.split(':')[1]
    return texture_path.split('/')[-1]


def build_aliases_from_jar(jar_path):
    if not os.path.exists(jar_path):
        print(f"[!] Error: File '{jar_path}' not found.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.normpath(os.path.join(script_dir, '..', 'texture_aliases.csv'))

    # 1. Use a dictionary of SETS to hold multiple aliases per item
    aliases = {}
    if os.path.exists(csv_path):
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    modern, legacy = row[0].strip(), row[1].strip()
                    if modern not in aliases: aliases[modern] = set()
                    aliases[modern].add(legacy)

    print(f"[*] Scanning models in {os.path.basename(jar_path)} for texture mappings...")
    added_count = 0

    with zipfile.ZipFile(jar_path, 'r') as jar:
        for file in jar.namelist():
            if file.startswith('assets/minecraft/models/') and file.endswith('.json'):
                model_name = file.split('/')[-1].replace('.json', '')
                try:
                    data = json.loads(jar.read(file).decode('utf-8'))
                    textures = data.get('textures', {})
                    found_texture = None

                    if 'layer0' in textures and isinstance(textures['layer0'], str) and not textures[
                        'layer0'].startswith('#'):
                        found_texture = extract_texture_name(textures['layer0'])
                    else:
                        for key, val in textures.items():
                            if isinstance(val, str) and not val.startswith('#') and 'particle' not in key:
                                found_texture = extract_texture_name(val)
                                break

                    # 2. Add new aliases to the set without overwriting old ones
                    if found_texture and found_texture != model_name:
                        if model_name not in aliases: aliases[model_name] = set()
                        if found_texture not in aliases[model_name]:
                            aliases[model_name].add(found_texture)
                            added_count += 1
                except Exception:
                    pass

    # 3. Write multiple rows per item if needed
    with open(csv_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['modern_name', 'legacy_texture_name'])
        for modern, legacy_set in sorted(aliases.items()):
            for legacy in sorted(legacy_set):
                writer.writerow([modern, legacy])

    print(f"✅ Successfully added {added_count} new mappings to texture_aliases.csv!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_texture_aliases.py <path_to_jar>")
    else:
        build_aliases_from_jar(sys.argv[1])