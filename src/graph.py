import networkx as nx


def build_graph(recipe_edges, tag_edges):
    """Builds a Directed Graph from parsed edges."""
    G = nx.DiGraph()

    for u, v in recipe_edges:
        G.add_edge(u, v)

    for child, tag in tag_edges:
        G.add_edge(child, tag)

    return G


def calculate_community_data(G):
    """Computes Louvain Modularity communities and Out-Degree centrality metrics."""
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

        nodes_data.append({
            "id": node,
            "label": node,
            "value": (degree * 3) + 10,
            "group": community_id,
            "degree": degree,
            "title": f"<b>{node}</b><br>Utility (Out-Degree): {degree}<br>Cluster ID: {community_id}"
        })

    edges_data = [{"from": u, "to": v, "arrows": "to"} for u, v in G.edges()]

    return nodes_data, edges_data