import json


def export_interactive_html(nodes_data, edges_data, output_file="minecraft_map.html"):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Minecraft Crafting Map</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            margin: 0;
            padding: 0;
            background-color: #121212;
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        #sidebar {{
            width: 380px;
            min-width: 380px;
            background-color: #1e1e1e;
            padding: 20px;
            box-shadow: 2px 0 12px rgba(0,0,0,0.6);
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
            z-index: 10;
            box-sizing: border-box;
        }}
        #mynetwork {{
            flex-grow: 1;
            height: 100%;
        }}
        h2 {{ 
            margin-top: 0; 
            font-size: 1.1rem; 
            border-bottom: 1px solid #333; 
            padding-bottom: 8px; 
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        select {{
            width: 100%;
            padding: 10px;
            background-color: #2a2a2a;
            color: #ffffff;
            border: 1px solid #444;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            box-sizing: border-box;
        }}
        select:focus {{ outline: none; border-color: #007acc; }}

        /* Tooltip Styles */
        .info-tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
            background: #333;
            color: #00d2ff;
            border-radius: 50%;
            width: 18px;
            height: 18px;
            text-align: center;
            line-height: 18px;
            font-size: 0.75rem;
            font-weight: bold;
        }}
        .info-tooltip .tooltip-text {{
            visibility: hidden;
            width: 240px;
            background-color: #282828;
            color: #e0e0e0;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 100;
            bottom: 125%;
            right: 0;
            opacity: 0;
            transition: opacity 0.2s;
            font-size: 0.8rem;
            font-weight: normal;
            line-height: 1.4;
            border: 1px solid #444;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.5);
            pointer-events: none;
        }}
        .info-tooltip:hover .tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}

        /* OVERRIDE VIS.JS DEFAULT TABLE CONTROL STYLES (Fixes white-on-white & horizontal scroll) */
        #config-panel table {{
            width: 100% !important;
            border-collapse: collapse !important;
        }}
        #config-panel tr {{
            display: flex !important;
            flex-direction: column !important;
            margin-bottom: 12px !important;
            background-color: #252525 !important;
            padding: 10px !important;
            border-radius: 6px !important;
            border: 1px solid #333 !important;
        }}
        #config-panel td {{
            display: block !important;
            width: 100% !important;
            padding: 2px 0 !important;
            color: #e0e0e0 !important;
            font-size: 0.85rem !important;
        }}
        #config-panel input[type="range"] {{
            width: 100% !important;
            accent-color: #007acc;
            margin-top: 6px;
        }}
        #config-panel input[type="checkbox"] {{
            accent-color: #007acc;
            transform: scale(1.2);
        }}
        .vis-configuration-wrapper {{
            color: #e0e0e0 !important;
        }}
        .vis-config-header {{
            font-weight: bold !important;
            color: #00d2ff !important;
            margin-bottom: 6px !important;
        }}
        .vis-config-label {{
            color: #cccccc !important;
        }}
        .vis-config-value {{
            color: #00d2ff !important;
            font-weight: bold !important;
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div>
            <h2>
                Ecosystem Isolation
                <span class="info-tooltip">?
                    <span class="tooltip-text">
                        <b>Louvain Modularity:</b> Groups items into clusters based on crafting connectivity density. Isolates distinct ecosystems like Redstone, Wood, or Dyes.
                    </span>
                </span>
            </h2>
            <select id="clusterSelect">
                <option value="all">Show All Clusters (Entire Map)</option>
            </select>
        </div>

        <div>
            <h2>
                Simulation Physics
                <span class="info-tooltip">?
                    <span class="tooltip-text">
                        <b>Barnes-Hut Engine:</b><br>
                        • <i>Gravity:</i> Node repulsion force.<br>
                        • <i>Central Gravity:</i> Pull toward screen center.<br>
                        • <i>Spring Length:</i> Desired edge distance.<br>
                        • <i>Damping:</i> Velocity decay rate.
                    </span>
                </span>
            </h2>
            <div id="config-panel"></div>
        </div>
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        var rawNodes = {json.dumps(nodes_data)};
        var rawEdges = {json.dumps(edges_data)};

        var nodeSet = new vis.DataSet(rawNodes);
        var edgeSet = new vis.DataSet(rawEdges);

        // Build Dropdown
        var groups = [...new Set(rawNodes.map(item => item.group))].sort((a, b) => a - b);
        var select = document.getElementById("clusterSelect");

        groups.forEach(groupId => {{
            var count = rawNodes.filter(n => n.group === groupId).length;
            var opt = document.createElement('option');
            opt.value = groupId;
            opt.innerHTML = "Cluster " + groupId + " (" + count + " items)";
            select.appendChild(opt);
        }});

        // Dynamic Filtering
        var nodeFilterValue = 'all';
        var nodesView = new vis.DataView(nodeSet, {{
            filter: function (item) {{
                return nodeFilterValue === 'all' || item.group == nodeFilterValue;
            }}
        }});

        select.addEventListener('change', (e) => {{
            nodeFilterValue = e.target.value;
            nodesView.refresh();
        }});

        // Network Setup
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: nodesView, edges: edgeSet }};

        var options = {{
            nodes: {{
                shape: 'dot',
                font: {{ color: '#ffffff', size: 13 }},
                borderWidth: 1,
                borderWidthSelected: 3
            }},
            edges: {{
                color: {{ inherit: 'from', opacity: 0.4 }},
                smooth: {{ type: 'continuous' }}
            }},
            physics: {{
                barnesHut: {{
                    gravity: -5000,
                    centralGravity: 0.3,
                    springLength: 150,
                    springStrength: 0.04,
                    damping: 0.09
                }}
            }},
            configure: {{
                filter: 'physics',
                container: document.getElementById('config-panel'),
                showButton: false
            }}
        }};

        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Interactive map exported successfully to: {output_file}")