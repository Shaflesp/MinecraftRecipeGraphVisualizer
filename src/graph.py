import networkx as nx
import os


def build_graph(recipe_edges, tag_edges):
    """Builds a Directed Graph from parsed edges."""
    G = nx.DiGraph()
    for u, v in recipe_edges: G.add_edge(u, v)
    for child, tag in tag_edges: G.add_edge(child, tag)
    return G


def get_icon_path(node_id, icons_dir="icons"):
    """Locates the extracted image for a given block or item with intelligent fallbacks."""
    search_id = node_id

    # 1. Hardcoded explicit aliases
    aliases = {
        "mangrove_roots": "mangrove_roots_top",
        "muddy_mangrove_roots": "muddy_mangrove_roots_top",
        "crimson_hyphae": "crimson_stem",
        "warped_hyphae": "warped_stem",
        "stripped_crimson_hyphae": "stripped_crimson_stem",
        "stripped_warped_hyphae": "stripped_warped_stem",
        "snow_block": "snow"
    }

    if search_id in aliases:
        search_id = aliases[search_id]

    def check(name):
        ipath = f"{icons_dir}/item/{name}.png"
        bpath = f"{icons_dir}/block/{name}.png"
        if os.path.exists(ipath): return ipath
        if os.path.exists(bpath): return bpath
        return None

    # 2. Try the exact match first
    found = check(search_id)
    if found: return found

    # 3. Smart Heuristic A: Try common block faces
    # This automatically fixes Pumpkins, Targets, Hay Blocks, Azaleas, Crafting Tables, etc.
    for suffix in ['_side', '_top', '_front']:
        found = check(search_id + suffix)
        if found: return found

    # 4. Smart Heuristic B: Wood conversions
    if search_id.endswith('_wood'):
        found = check(search_id.replace('_wood', '_log'))
        if found: return found

    # 5. Smart Heuristic C: Architectural derivations (Walls, Fences, Slabs, Stairs)
    # This strips the architectural suffix and hunts for the base material texture
    for suffix in ['_wall', '_fence', '_fence_gate', '_slab', '_stairs']:
        if search_id.endswith(suffix):
            base = search_id.replace(suffix, '')

            # Try direct base (e.g., cobblestone_wall -> cobblestone.png)
            found = check(base)
            if found: return found

            # Try plural base (e.g., stone_brick_stairs -> stone_bricks.png)
            found = check(base + 's')
            if found: return found

            # Try planks (e.g., oak_fence -> oak_planks.png)
            found = check(base + '_planks')
            if found: return found

    return None


def calculate_community_data(G, use_icons=False):
    """Computes Louvain Modularity and applies icons if enabled."""
    undirected_G = G.to_undirected()
    communities = list(nx.community.louvain_communities(undirected_G))
    out_degrees = dict(G.out_degree())

    nodes_data = []
    for node in G.nodes():
        degree = out_degrees.get(node, 0)

        community_id = 0
        for i, comm in enumerate(communities):
            if node in comm:
                community_id = i
                break

        node_dict = {
            "id": node,
            "label": node,
            "value": (degree * 4) + 12,  # Slightly larger base size for images
            "group": community_id,
            "degree": degree,
            "title": f"<b>{node}</b><br>Utility (Out-Degree): {degree}<br>Cluster ID: {community_id}"
        }

        # Apply Minecraft icons if available
        if use_icons and not node.startswith('#'):
            icon = get_icon_path(node)
            if icon:
                node_dict["shape"] = "image"
                node_dict["image"] = icon

        nodes_data.append(node_dict)

    edges_data = [{"from": u, "to": v, "arrows": "to"} for u, v in G.edges()]
    return nodes_data, edges_data


def calculate_graph_metrics(G):
    """Calculates gameplay-focused network metrics using strict structural graph rules."""

    # 1. Global Topology
    network_stats = [
        ("Total Items (Nodes)", G.number_of_nodes()),
        ("Total Recipes (Edges)", G.number_of_edges()),
        ("Network Density", f"{nx.density(G):.4f}")
    ]

    # 2. Highest Utility (Out-Degree: Used in the most recipes)
    out_degrees = sorted(G.out_degree(), key=lambda x: x[1], reverse=True)
    top_utility = out_degrees[:10]

    # 3. Crafting Complexity (Max Crafting Depth)
    DAG = nx.condensation(G)
    depths = {}
    for scc_id in nx.topological_sort(DAG):
        preds = list(DAG.predecessors(scc_id))
        if not preds:
            depths[scc_id] = 1
        else:
            depths[scc_id] = 1 + max(depths[p] for p in preds)

    item_complexities = []
    for scc_id, data in DAG.nodes(data=True):
        scc_depth = depths[scc_id]
        for node in data['members']:
            if not node.startswith('#'):
                item_complexities.append((node, scc_depth))

    top_crafted = sorted(item_complexities, key=lambda x: x[1], reverse=True)[:10]

    # 4. Strict Ecosystem Subsumption Model
    all_reach = []
    for node in G.nodes():
        if not node.startswith('#'):
            descendants = nx.descendants(G, node)
            if len(descendants) > 0:
                all_reach.append((node, descendants))

    all_reach.sort(key=lambda x: len(x[1]), reverse=True)

    seen_groups = []  # list of [node_names, union_desc_set]

    for node, desc_set in all_reach:
        is_fused = False

        for group in seen_groups:
            group_nodes, group_desc_set = group

            intersection = len(desc_set.intersection(group_desc_set))
            union_size = len(desc_set.union(group_desc_set))

            # RULE A (Hierarchical Subsumption):
            # If >= 85% of this item's tree is already inside the group's tree, it is a sub-component.
            # (e.g., Oak Planks, Bamboo, and Wood Slabs are all subsets of the overarching Wood tree).
            subset_ratio = intersection / len(desc_set) if len(desc_set) > 0 else 0

            # RULE B (Sibling Equivalence):
            # If they share >= 65% of their total combined tree (e.g., Oak Log vs Birch Log).
            jaccard = intersection / union_size if union_size > 0 else 0

            if subset_ratio > 0.85 or jaccard > 0.65:
                group_nodes.append(node)
                group[1] = group_desc_set.union(desc_set)
                is_fused = True
                break

        if not is_fused:
            seen_groups.append([[node], set(desc_set)])

    # Format output & apply deterministic naming hierarchy
    self_sustaining = []
    for group_nodes, union_desc_set in seen_groups[:10]:

        def name_score(name):
            in_deg = G.in_degree(name)
            out_deg = G.out_degree(name)

            penalty = 1 if ('stripped' in name or 'waxed' in name) else 0

            return (in_deg, penalty, -out_deg, len(name), name)

        group_nodes.sort(key=name_score)
        primary_name = group_nodes[0].replace('_', ' ').title()

        # Explicitly label it as a "Family" since it represents the combined tree
        if len(group_nodes) > 1:
            label = f"{primary_name} Family"
        else:
            label = primary_name

        self_sustaining.append((label, len(union_desc_set)))

    return {
        "network_stats": network_stats,
        "top_utility": top_utility,
        "top_crafted": top_crafted,
        "self_sustaining": self_sustaining
    }