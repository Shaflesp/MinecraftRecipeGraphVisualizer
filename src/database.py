import sqlite3
import json
import os


def init_db(db_path):
    """Initializes the SQLite database and creates the schema if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Versions Table
    c.execute('''CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_name TEXT UNIQUE,
                    metrics_json TEXT
                 )''')

    # Nodes Table
    c.execute('''CREATE TABLE IF NOT EXISTS nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id INTEGER,
                    node_id TEXT,
                    label TEXT,
                    value INTEGER,
                    group_id INTEGER,
                    degree INTEGER,
                    title TEXT,
                    shape TEXT,
                    image TEXT,
                    FOREIGN KEY(version_id) REFERENCES versions(id)
                 )''')

    # Edges (Recipes) Table
    c.execute('''CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id INTEGER,
                    from_node TEXT,
                    to_node TEXT,
                    arrows TEXT,
                    FOREIGN KEY(version_id) REFERENCES versions(id)
                 )''')

    conn.commit()
    return conn


def save_version_data(db_path, version_name, nodes_data, edges_data, metrics_data):
    """Saves the parsed graph and metrics to SQLite, overwriting if the version already exists."""
    conn = init_db(db_path)
    c = conn.cursor()

    c.execute("SELECT id FROM versions WHERE version_name = ?", (version_name,))
    row = c.fetchone()
    if row:
        version_id = row[0]
        c.execute("DELETE FROM nodes WHERE version_id = ?", (version_id,))
        c.execute("DELETE FROM edges WHERE version_id = ?", (version_id,))
        c.execute("UPDATE versions SET metrics_json = ? WHERE id = ?", (json.dumps(metrics_data), version_id))
    else:
        c.execute("INSERT INTO versions (version_name, metrics_json) VALUES (?, ?)",
                  (version_name, json.dumps(metrics_data)))
        version_id = c.lastrowid

    # Insert Nodes
    nodes_tuples = []
    for n in nodes_data:
        nodes_tuples.append((
            version_id, n.get('id'), n.get('label'), n.get('value'),
            n.get('group'), n.get('degree'), n.get('title'),
            n.get('shape'), n.get('image')
        ))

    c.executemany("""INSERT INTO nodes 
                     (version_id, node_id, label, value, group_id, degree, title, shape, image) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", nodes_tuples)

    # Insert Edges
    edges_tuples = [(version_id, e.get('from'), e.get('to'), e.get('arrows', 'to')) for e in edges_data]
    c.executemany("INSERT INTO edges (version_id, from_node, to_node, arrows) VALUES (?, ?, ?, ?)", edges_tuples)

    conn.commit()
    conn.close()


def load_version_data(db_path, version_name):
    """Fetches a specific Minecraft version's map from the database to inject into HTML."""
    if not os.path.exists(db_path):
        return None, None, None

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT id, metrics_json FROM versions WHERE version_name = ?", (version_name,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None, None, None

    version_id, metrics_json = row
    metrics_data = json.loads(metrics_json) if metrics_json else {}

    # Reconstruct Nodes list of dictionaries
    c.execute("SELECT node_id, label, value, group_id, degree, title, shape, image FROM nodes WHERE version_id = ?",
              (version_id,))
    nodes_data = []
    for n in c.fetchall():
        node_dict = {
            "id": n[0], "label": n[1], "value": n[2],
            "group": n[3], "degree": n[4], "title": n[5]
        }
        if n[6]: node_dict["shape"] = n[6]
        if n[7]: node_dict["image"] = n[7]
        nodes_data.append(node_dict)

    # Reconstruct Edges list of dictionaries
    c.execute("SELECT from_node, to_node, arrows FROM edges WHERE version_id = ?", (version_id,))
    edges_data = [{"from": e[0], "to": e[1], "arrows": e[2]} for e in c.fetchall()]

    conn.close()
    return nodes_data, edges_data, metrics_data