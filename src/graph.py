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