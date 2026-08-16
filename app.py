from flask import Flask, jsonify, render_template, send_from_directory
import sqlite3
import os
import json
from src.database import load_version_data

app = Flask(__name__)
DB_PATH = 'minecraft_data.db'

def get_versions():
    """Fetches all stored versions from the database, sorted chronologically."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Sort by ID assuming they were parsed in order
    c.execute("SELECT version_name FROM versions ORDER BY id ASC")
    versions = [r[0] for r in c.fetchall()]
    conn.close()
    return versions

@app.route('/')
def index():
    """Serves the main HTML interface."""
    return render_template('index.html')

@app.route('/api/versions')
def api_versions():
    """Returns a list of all available versions."""
    return jsonify(get_versions())

@app.route('/api/graph/<version>')
def api_graph(version):
    """Returns the nodes, edges, and metrics for a specific version."""
    nodes, edges, metrics = load_version_data(DB_PATH, version)
    if not nodes:
        return jsonify({"error": "Version not found"}), 404
    return jsonify({"nodes": nodes, "edges": edges, "metrics": metrics})

@app.route('/icons/<path:filename>')
def serve_icons(filename):
    """Serves the extracted Minecraft textures to the frontend."""
    return send_from_directory('icons', filename)


@app.route('/compare')
def compare():
    """Serves the comparative analytics dashboard."""
    return render_template('compare.html')


@app.route('/api/compare_data')
def api_compare_data():
    """Fetches the metrics for all versions chronologically."""
    if not os.path.exists(DB_PATH):
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT version_name, metrics_json FROM versions ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    historical_data = []
    for row in rows:
        version_name, metrics_raw = row
        metrics = json.loads(metrics_raw) if metrics_raw else {}
        historical_data.append({
            "version": version_name,
            "metrics": metrics
        })

    return jsonify(historical_data)

if __name__ == '__main__':
    print("Starting Minecraft Ecosystem Server...")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True)