import networkx as nx
import os


def build_graph(recipe_edges, tag_edges):
    """Builds a Directed Graph from parsed edges."""
    G = nx.DiGraph()
    for u, v in recipe_edges: G.add_edge(u, v)
    for child, tag in tag_edges: G.add_edge(child, tag)
    return G


def get_icon_path(node_id, icons_dir="icons/assets/minecraft/textures"):
    """Locates the extracted image for a given block or item."""
    item_path = f"{icons_dir}/item/{node_id}.png"
    block_path = f"{icons_dir}/block/{node_id}.png"

    if os.path.exists(item_path): return item_path
    if os.path.exists(block_path): return block_path
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
    """Calculates gameplay-focused network metrics based on the current graph."""

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
    # We use DAG Condensation to collapse infinite dye/block loops into single steps
    DAG = nx.condensation(G)
    depths = {}

    for scc_id in nx.topological_sort(DAG):
        preds = list(DAG.predecessors(scc_id))
        if not preds:
            depths[scc_id] = 1
        else:
            depths[scc_id] = 1 + max(depths[p] for p in preds) # Add 1 step to the longest prerequisite

    item_complexities = []
    for scc_id, data in DAG.nodes(data=True):
        scc_depth = depths[scc_id]
        for node in data['members']:
            if not node.startswith('#'):
                item_complexities.append((node, scc_depth))

    top_crafted = sorted(item_complexities, key=lambda x: x[1], reverse=True)[:10]

    # 4. Self-Sustenance (Material Ecosystem Reach)
    # Calculates exactly how many unique items exist in the downstream tree of a base material
    base_materials = ['oak_log', 'iron_ingot', 'copper_ingot', 'redstone', 'cobblestone', 'netherite_ingot', 'diamond', 'gold_ingot']
    reach_data = []
    for mat in base_materials:
        if mat in G:
            desc_count = len(nx.descendants(G, mat))
            reach_data.append((mat.replace('_', ' ').title(), desc_count))

    self_sustaining = sorted(reach_data, key=lambda x: x[1], reverse=True)

    return {
        "network_stats": network_stats,
        "top_utility": top_utility,
        "top_crafted": top_crafted,
        "self_sustaining": self_sustaining
    }