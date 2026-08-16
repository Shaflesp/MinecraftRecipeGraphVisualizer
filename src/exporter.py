import json


def export_interactive_html(nodes_data, edges_data, metrics_data=None, output_file="minecraft_map.html"):
    if not metrics_data:
        metrics_data = {
            "network_stats": [("Total Items", len(nodes_data)), ("Total Recipes", len(edges_data))],
            "top_utility": [("No Data", "-")],
            "self_sustaining": [("No Data", "-")],
            "top_crafted": [("No Data", "-")]
        }

    def build_rows(data_list):
        return "".join([f"<tr><td>{k}</td><td class='val-col'>{v}</td></tr>" for k, v in data_list])

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Minecraft Crafting Ecosystem</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        :root {{
            --bg-main: #121212;
            --bg-panel: rgba(30, 30, 30, 0.95);
            --bg-input: #2a2a2a;
            --accent: #007acc;
            --text-main: #e0e0e0;
            --border-color: #444444;
        }}

        body {{
            margin: 0; padding: 0;
            background-color: var(--bg-main); color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            overflow: hidden;
        }}

        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #555; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #777; }}

        #mynetwork {{
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            width: 100vw; height: 100vh; z-index: 1;
        }}

        .panel {{
            position: absolute; top: 0; bottom: 0; width: 360px;
            background-color: var(--bg-panel); backdrop-filter: blur(8px);
            padding: 25px 20px; display: flex; flex-direction: column; gap: 25px;
            overflow-y: auto; z-index: 10; box-sizing: border-box;
            transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}

        #sidebar-left {{ left: 0; border-right: 1px solid var(--border-color); box-shadow: 4px 0 25px rgba(0,0,0,0.8); transform: translateX(0); }}
        #sidebar-left.collapsed {{ transform: translateX(-100%); }}

        #sidebar-right {{ right: 0; border-left: 1px solid var(--border-color); box-shadow: -4px 0 25px rgba(0,0,0,0.8); transform: translateX(100%); }}
        #sidebar-right.open {{ transform: translateX(0); }}

        .btn {{
            background-color: var(--bg-input); color: var(--text-main);
            border: 1px solid var(--border-color); border-radius: 6px;
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            transition: all 0.2s ease;
        }}
        .btn:hover {{ background-color: #3a3a3a; color: white; border-color: var(--accent); }}

        .floating-btn {{
            position: absolute; top: 20px; width: 45px; height: 45px;
            font-size: 1.5rem; z-index: 5; box-shadow: 0 4px 15px rgba(0,0,0,0.6);
            opacity: 0; visibility: hidden; transition: opacity 0.3s ease, visibility 0.3s ease;
        }}
        .floating-btn.visible {{ opacity: 1; visibility: visible; z-index: 15; }}

        #open-btn-left {{ left: 20px; }}
        #open-btn-right {{ right: 20px; }}

        .panel-header {{
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 5px; padding-bottom: 15px; border-bottom: 1px solid var(--border-color);
        }}
        .panel-header h1 {{ margin: 0; font-size: 1.3rem; font-weight: 600; color: white; }}
        .close-btn {{ width: 32px; height: 32px; font-size: 1rem; }}

        h2 {{ margin: 0 0 12px 0; font-size: 1rem; color: var(--accent); }}

        .data-table {{
            width: 100%; border-collapse: collapse; font-size: 0.9rem;
            background: rgba(0,0,0,0.2); border-radius: 8px; overflow: hidden;
            border: 1px solid #333;
        }}
        .data-table th, .data-table td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #333; }}
        .data-table tr:last-child td {{ border-bottom: none; }}
        .data-table th {{ background: rgba(0,0,0,0.4); color: var(--accent); font-weight: 600; font-size: 0.85rem; }}
        .val-col {{ text-align: right !important; font-family: monospace; font-weight: bold; color: #fff; }}

        select, input[type=text], input[type=range] {{
            width: 100%; padding: 10px; background-color: var(--bg-input); color: #ffffff;
            border: 1px solid var(--border-color); border-radius: 6px; box-sizing: border-box; cursor: pointer;
        }}
        input[type=text] {{ cursor: text; font-family: monospace; }}
        input[type=text]:focus, select:focus {{ outline: none; border-color: var(--accent); }}

        .control-group {{ background: rgba(0,0,0,0.2); border: 1px solid #333; border-radius: 8px; padding: 12px; }}
        .slider-row {{ margin-bottom: 12px; }}
        .slider-row:last-child {{ margin-bottom: 0; }}
        .slider-label {{ display: flex; justify-content: space-between; font-size: 0.85rem; color: #bbb; margin-bottom: 6px; }}
        .slider-val {{ color: var(--accent); font-weight: bold; font-family: monospace; }}

        .flex-row {{ display: flex; gap: 8px; margin-top: 8px; }}
        .flex-row .btn {{ flex: 1; padding: 8px; font-size: 0.9rem; }}
    </style>
</head>
<body>

    <button id="open-btn-left" class="btn floating-btn">☰</button>
    <button id="open-btn-right" class="btn floating-btn visible">📊</button>

    <!-- LEFT PANEL: Controls -->
    <div id="sidebar-left" class="panel">
        <div class="panel-header">
            <h1>Map Controls</h1>
            <button id="close-btn-left" class="btn close-btn">✕</button>
        </div>

        <div>
            <h2>Branch Isolation</h2>
            <div class="control-group" style="padding: 10px;">
                <input type="text" id="search-input" list="item-list" placeholder="e.g. oak_log" autocomplete="off">
                <select id="isolation-mode" style="margin-top: 8px;">
                    <option value="upstream">Show Prerequisites (Trace Backward)</option>
                    <option value="downstream">Show What It Crafts (Trace Forward)</option>
                </select>
                <datalist id="item-list"></datalist>
                <div class="flex-row">
                    <button id="btn-isolate" class="btn">Isolate Tree</button>
                    <button id="btn-reset" class="btn">Reset View</button>
                </div>
            </div>
        </div>

        <div>
            <h2>Ecosystem Filter</h2>
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

    <!-- RIGHT PANEL: Metrics -->
    <div id="sidebar-right" class="panel">
        <div class="panel-header">
            <h1>Network Analytics</h1>
            <button id="close-btn-right" class="btn close-btn">✕</button>
        </div>
        <div>
            <h2>Global Topology</h2>
            <table class="data-table">
                {build_rows(metrics_data['network_stats'])}
            </table>
        </div>
        <div>
            <h2>Highest Utility Nodes</h2>
            <table class="data-table">
                <tr><th>Item Name</th><th class="val-col">Out-Degree</th></tr>
                {build_rows(metrics_data['top_utility'])}
            </table>
        </div>
        <div>
            <h2>Material Ecosystem Reach</h2>
            <table class="data-table">
                <tr><th>Root Material</th><th class="val-col">Downstream Tree</th></tr>
                {build_rows(metrics_data.get('self_sustaining', []))}
            </table>
        </div>
        <div>
            <h2>Crafting Complexity (Depth)</h2>
            <table class="data-table">
                <tr><th>Item Name</th><th class="val-col">Required Steps</th></tr>
                {build_rows(metrics_data.get('top_crafted', []))}
            </table>
        </div>
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        // --- UI FOLDING LOGIC ---
        const panelLeft = document.getElementById('sidebar-left');
        const btnOpenLeft = document.getElementById('open-btn-left');
        const btnCloseLeft = document.getElementById('close-btn-left');

        const panelRight = document.getElementById('sidebar-right');
        const btnOpenRight = document.getElementById('open-btn-right');
        const btnCloseRight = document.getElementById('close-btn-right');

        btnCloseLeft.addEventListener('click', () => {{ panelLeft.classList.add('collapsed'); btnOpenLeft.classList.add('visible'); }});
        btnOpenLeft.addEventListener('click', () => {{ panelLeft.classList.remove('collapsed'); btnOpenLeft.classList.remove('visible'); }});
        btnCloseRight.addEventListener('click', () => {{ panelRight.classList.remove('open'); btnOpenRight.classList.add('visible'); }});
        btnOpenRight.addEventListener('click', () => {{ panelRight.classList.add('open'); btnOpenRight.classList.remove('visible'); }});

        // --- NETWORK DATA & INIT ---
        var rawNodes = {json.dumps(nodes_data)};
        var rawEdges = {json.dumps(edges_data)};

        var nodeSet = new vis.DataSet(rawNodes);
        var edgeSet = new vis.DataSet(rawEdges);

        var dataList = document.getElementById('item-list');
        rawNodes.forEach(n => {{
            var opt = document.createElement('option');
            opt.value = n.id;
            dataList.appendChild(opt);
        }});

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

        // FILTER LOGIC
        var nodeFilterValue = 'all';
        var isolatedNodes = null;

        var nodesView = new vis.DataView(nodeSet, {{
            filter: function (item) {{ 
                if (isolatedNodes && !isolatedNodes.has(item.id)) return false;
                if (nodeFilterValue !== 'all' && item.group != nodeFilterValue) return false;
                return true; 
            }}
        }});

        select.addEventListener('change', (e) => {{
            nodeFilterValue = e.target.value;
            isolatedNodes = null; 
            document.getElementById('search-input').value = '';
            network.unselectAll();
            nodesView.refresh();
        }});

        // ISOLATION LOGIC (Bi-directional Traversal)
        function traverseTree(targetId, mode) {{
            let visited = new Set();
            let queue = [targetId];
            visited.add(targetId);

            while(queue.length > 0) {{
                let current = queue.shift();

                let relevantEdges;
                if (mode === 'upstream') {{
                    // Backward: What does this item need? (Incoming edges)
                    relevantEdges = rawEdges.filter(e => e.to === current);
                    relevantEdges.forEach(e => {{
                        if(!visited.has(e.from)) {{
                            visited.add(e.from);
                            queue.push(e.from);
                        }}
                    }});
                }} else {{
                    // Forward: What can this item craft? (Outgoing edges)
                    relevantEdges = rawEdges.filter(e => e.from === current);
                    relevantEdges.forEach(e => {{
                        if(!visited.has(e.to)) {{
                            visited.add(e.to);
                            queue.push(e.to);
                        }}
                    }});
                }}
            }}
            return visited;
        }}

        document.getElementById('btn-isolate').addEventListener('click', () => {{
            let val = document.getElementById('search-input').value.trim();
            if (!nodeSet.get(val)) {{
                alert("Item not found in the crafting map!");
                return;
            }}

            let mode = document.getElementById('isolation-mode').value;

            isolatedNodes = traverseTree(val, mode);

            document.getElementById('clusterSelect').value = 'all';
            nodeFilterValue = 'all';

            nodesView.refresh();
            network.selectNodes([val]);
            network.fit({{ animation: true }});
        }});

        document.getElementById('btn-reset').addEventListener('click', () => {{
            isolatedNodes = null;
            document.getElementById('search-input').value = '';
            document.getElementById('clusterSelect').value = 'all';
            nodeFilterValue = 'all';
            nodesView.refresh();
            network.unselectAll();
            network.fit({{ animation: true }});
        }});

        var container = document.getElementById('mynetwork');
        var data = {{ nodes: nodesView, edges: edgeSet }};
        var options = {{
            nodes: {{ shape: 'dot', font: {{ color: '#ffffff', size: 14 }}, borderWidth: 1 }},
            edges: {{ color: {{ inherit: 'from', opacity: 0.5 }}, smooth: {{ type: 'continuous' }} }},
            physics: {{ 
                barnesHut: {{ 
                    gravity: -6000, 
                    springLength: 150,
                    damping: 0.1,
                    centralGravity: 0.4
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
            input.addEventListener('input', (e) => {{ val.textContent = e.target.value; updatePhysics(); }});
        }};

        bindSlider('in-gravity', 'val-gravity');
        bindSlider('in-spring', 'val-spring');
        bindSlider('in-damping', 'val-damping');
        bindSlider('in-central', 'val-central');

        document.getElementById('btn-stabilize').addEventListener('click', () => {{ network.stabilize(); }});
    </script>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Interactive map with bi-directional branch isolation exported successfully to: {output_file}")