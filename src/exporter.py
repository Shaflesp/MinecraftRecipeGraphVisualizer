import json


def export_interactive_html(nodes_data, edges_data, output_file="minecraft_map.html"):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Minecraft Crafting Ecosystem</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        :root {{
            --bg-main: #121212;
            --bg-sidebar: rgba(30, 30, 30, 0.95);
            --bg-input: #2a2a2a;
            --accent: #007acc;
            --accent-hover: #0098ff;
            --text-main: #e0e0e0;
            --border-color: #444444;
        }}

        body {{
            margin: 0;
            padding: 0;
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            overflow: hidden;
        }}

        /* Custom Dark Mode Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #555; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #777; }}

        /* Main Network Canvas (Takes Full Screen) */
        #mynetwork {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            width: 100vw;
            height: 100vh;
            z-index: 1;
        }}

        /* Floating Sidebar Container */
        #sidebar {{
            position: absolute;
            top: 0; left: 0; bottom: 0;
            width: 360px;
            background-color: var(--bg-sidebar);
            backdrop-filter: blur(8px); /* Nice glass effect over the graph */
            border-right: 1px solid var(--border-color);
            padding: 25px 20px;
            box-shadow: 4px 0 25px rgba(0,0,0,0.8);
            display: flex;
            flex-direction: column;
            gap: 25px;
            overflow-y: auto;
            z-index: 10;
            box-sizing: border-box;
            transform: translateX(0);
            transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}

        /* The "Folded" State */
        #sidebar.collapsed {{
            transform: translateX(-100%);
        }}

        /* Toggle Buttons */
        .btn {{
            background-color: var(--bg-input);
            color: var(--text-main);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}
        .btn:hover {{ background-color: #3a3a3a; color: white; border-color: var(--accent); }}

        #open-btn {{
            position: absolute;
            top: 20px;
            left: 20px;
            width: 45px;
            height: 45px;
            font-size: 1.5rem;
            z-index: 5;
            box-shadow: 0 4px 15px rgba(0,0,0,0.6);
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }}
        #open-btn.visible {{ opacity: 1; visibility: visible; z-index: 15; }}

        .sidebar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }}
        .sidebar-header h1 {{ margin: 0; font-size: 1.3rem; font-weight: 600; color: white; }}
        #close-btn {{ width: 32px; height: 32px; font-size: 1rem; }}

        h2 {{ margin: 0 0 12px 0; font-size: 1rem; color: var(--accent); }}

        select {{
            width: 100%;
            padding: 10px;
            background-color: var(--bg-input);
            color: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            box-sizing: border-box;
        }}
        select:focus {{ outline: none; border-color: var(--accent); }}

        /* Custom Slider UI */
        .control-group {{
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        }}
        .slider-row {{
            margin-bottom: 12px;
        }}
        .slider-row:last-child {{ margin-bottom: 0; }}
        .slider-label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            color: #bbb;
            margin-bottom: 6px;
        }}
        .slider-val {{ color: var(--accent); font-weight: bold; font-family: monospace; font-size: 0.95rem; }}
        input[type=range] {{
            width: 100%;
            margin: 0;
            accent-color: var(--accent);
            cursor: pointer;
        }}
    </style>
</head>
<body>

    <button id="open-btn" class="btn">☰</button>

    <div id="sidebar">
        <div class="sidebar-header">
            <h1>Map Controls</h1>
            <button id="close-btn" class="btn">✕</button>
        </div>

        <div>
            <h2>Data Filter</h2>
            <select id="clusterSelect">
                <option value="all">Show All Ecosystems</option>
            </select>
        </div>

        <div>
            <h2>Physics Engine</h2>
            <div class="control-group">
                <div class="slider-row">
                    <div class="slider-label"><span>Gravity</span> <span id="val-gravity" class="slider-val">-6000</span></div>
                    <input type="range" id="in-gravity" min="-10000" max="0" step="100" value="-6000">
                </div>
                <div class="slider-row">
                    <div class="slider-label"><span>Spring Length</span> <span id="val-spring" class="slider-val">150</span></div>
                    <input type="range" id="in-spring" min="10" max="1000" step="10" value="150">
                </div>
                <div class="slider-row">
                    <div class="slider-label"><span>Damping</span> <span id="val-damping" class="slider-val">0.10</span></div>
                    <input type="range" id="in-damping" min="0" max="1" step="0.05" value="0.10">
                </div>
                <div class="slider-row">
                    <div class="slider-label"><span>Central Gravity</span> <span id="val-central" class="slider-val">0.4</span></div>
                    <input type="range" id="in-central" min="0" max="2" step="0.1" value="0.4">
                </div>
            </div>
            <button id="btn-stabilize" class="btn" style="width:100%; padding: 10px; font-weight:bold; margin-top: 5px;">Force Stabilization</button>
        </div>
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        // --- UI FOLDING LOGIC ---
        const sidebar = document.getElementById('sidebar');
        const openBtn = document.getElementById('open-btn');
        const closeBtn = document.getElementById('close-btn');

        closeBtn.addEventListener('click', () => {{
            sidebar.classList.add('collapsed');
            openBtn.classList.add('visible');
        }});
        openBtn.addEventListener('click', () => {{
            sidebar.classList.remove('collapsed');
            openBtn.classList.remove('visible');
        }});

        // --- NETWORK DATA & INIT ---
        var rawNodes = {json.dumps(nodes_data)};
        var rawEdges = {json.dumps(edges_data)};

        var nodeSet = new vis.DataSet(rawNodes);
        var edgeSet = new vis.DataSet(rawEdges);

        var groups = [...new Set(rawNodes.map(item => item.group))].sort((a, b) => a - b);
        var select = document.getElementById("clusterSelect");

        groups.forEach(groupId => {{
            var count = rawNodes.filter(n => n.group === groupId).length;
            if(count > 0) {{
                var opt = document.createElement('option');
                opt.value = groupId;
                opt.innerHTML = "Cluster " + groupId + " (" + count + " items)";
                select.appendChild(opt);
            }}
        }});

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

        var container = document.getElementById('mynetwork');
        var data = {{ nodes: nodesView, edges: edgeSet }};

        var options = {{
            nodes: {{
                shape: 'dot',
                font: {{ color: '#ffffff', size: 14 }},
                borderWidth: 1,
                borderWidthSelected: 3
            }},
            edges: {{
                color: {{ inherit: 'from', opacity: 0.5 }},
                smooth: {{ type: 'continuous' }}
            }},
            physics: {{
                barnesHut: {{
                    gravity: -6000,
                    centralGravity: 0.4,
                    springLength: 150,
                    damping: 0.1
                }}
            }}
        }};

        var network = new vis.Network(container, data, options);

        // --- CUSTOM PHYSICS BINDING ---
        const updatePhysics = () => {{
            network.setOptions({{
                physics: {{
                    barnesHut: {{
                        gravity: Number(document.getElementById('in-gravity').value),
                        springLength: Number(document.getElementById('in-spring').value),
                        damping: Number(document.getElementById('in-damping').value),
                        centralGravity: Number(document.getElementById('in-central').value)
                    }}
                }}
            }});
        }};

        const bindSlider = (inputId, valId) => {{
            const input = document.getElementById(inputId);
            const val = document.getElementById(valId);
            input.addEventListener('input', (e) => {{
                val.textContent = e.target.value;
                updatePhysics();
            }});
        }};

        bindSlider('in-gravity', 'val-gravity');
        bindSlider('in-spring', 'val-spring');
        bindSlider('in-damping', 'val-damping');
        bindSlider('in-central', 'val-central');

        document.getElementById('btn-stabilize').addEventListener('click', () => {{
            network.stabilize();
        }});
    </script>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Interactive map exported successfully to: {output_file}")