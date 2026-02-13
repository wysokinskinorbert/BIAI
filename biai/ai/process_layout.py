"""Server-side layout calculation (topological sort, Dagre-like)."""


def calculate_layout(
    nodes: list[dict],
    edges: list[dict],
    direction: str = "TB",
    node_width: int = 180,
    node_height: int = 60,
    rank_sep: int = 80,
    node_sep: int = 40,
) -> list[dict]:
    """Calculate node positions using topological sort + layered layout.

    Assigns x/y positions to each node based on graph layers (Kahn's algorithm).
    Auto-switches to LR (horizontal) layout when the graph is a chain
    (max 1 node per layer with 3+ layers) to avoid tall narrow layouts.

    Returns updated nodes with calculated positions.
    """
    if not nodes:
        return nodes

    layers = _compute_layers(nodes, edges)

    # Adaptive direction: chains (max 1 node per layer, 3+ layers) → LR
    max_layer_width = max(len(layer) for layer in layers) if layers else 1
    num_layers = len(layers)
    if direction == "TB" and max_layer_width <= 1 and num_layers > 3:
        direction = "LR"

    # Assign positions
    pos: dict[str, dict] = {}
    for li, layer in enumerate(layers):
        for ni, nid in enumerate(layer):
            if direction == "TB":
                x = ni * (node_width + node_sep) - (len(layer) - 1) * (node_width + node_sep) / 2
                y = li * (node_height + rank_sep)
            else:  # LR
                x = li * (node_width + rank_sep)
                y = ni * (node_height + node_sep) - (len(layer) - 1) * (node_height + node_sep) / 2
            pos[nid] = {"x": x, "y": y}

    for node in nodes:
        if node["id"] in pos:
            node["position"] = pos[node["id"]]

    return nodes


def _compute_layers(nodes: list[dict], edges: list[dict]) -> list[list[str]]:
    """Compute topological layers using Kahn's algorithm."""
    adj: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}
    node_ids = {n["id"] for n in nodes}

    for nid in node_ids:
        adj[nid] = []
        in_degree[nid] = 0

    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in adj and tgt in in_degree:
            adj[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    layers: list[list[str]] = []
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    visited: set[str] = set()

    while queue:
        layers.append(queue[:])
        next_queue = []
        for nid in queue:
            visited.add(nid)
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and neighbor not in visited:
                    next_queue.append(neighbor)
        queue = next_queue

    # Unvisited nodes (cycles) → last layer
    unvisited = [nid for nid in node_ids if nid not in visited]
    if unvisited:
        layers.append(unvisited)

    return layers
