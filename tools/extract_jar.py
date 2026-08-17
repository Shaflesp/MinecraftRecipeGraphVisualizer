import os
import sys
import zipfile


def extract_jar(version, jar_path):
    if not os.path.exists(jar_path):
        print(f"[!] Error: File '{jar_path}' not found.")
        return

    # Bulletproof path generation to the /dumps/ folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dump_dir = os.path.normpath(os.path.join(script_dir, "..", "dumps", version))

    print(f"[*] Analyzing {jar_path}...")

    # We strictly filter what we extract to keep the dump folder small and fast
    target_prefixes = [
        'data/minecraft/recipes/',
        'data/minecraft/recipe/',
        'assets/minecraft/recipes/',
        'data/minecraft/tags/items/',
        'data/minecraft/tags/item/',
        'assets/minecraft/textures/item/',
        'assets/minecraft/textures/block/',
        'assets/minecraft/textures/items/',
        'assets/minecraft/textures/blocks/'
    ]

    extracted_count = 0
    os.makedirs(dump_dir, exist_ok=True)

    with zipfile.ZipFile(jar_path, 'r') as jar:
        for file in jar.namelist():
            # Check if the file is in our target list and is an actual file (not a folder path)
            if any(file.startswith(prefix) for prefix in target_prefixes) and not file.endswith('/'):
                jar.extract(file, dump_dir)
                extracted_count += 1

    if extracted_count > 0:
        print(f"✅ Successfully extracted {extracted_count} files to /dumps/{version}/!")
    else:
        print(f"[!] No recipes, tags, or textures found. Are you sure this is a client .jar?")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_jar.py <version> <path_to_jar>")
        print(
            "Example: python extract_jar.py 1.20.4 C:/Users/Name/AppData/Roaming/.minecraft/versions/1.20.4/1.20.4.jar")
    else:
        extract_jar(sys.argv[1], sys.argv[2])