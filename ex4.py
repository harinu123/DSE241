import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.title("Bighorn Sheep Dominance Network Visualization from GraphML")

st.markdown("""
This interactive visualization displays the dominance relationships among bighorn sheep.
The graph data is loaded from a GraphML file (sheep_ml.graphml.xml) that includes:
- A node attribute `age`
- An edge attribute `weight`

Nodes are augmented with computed in-degree and out-degree metrics. Hover over a node to see details.
""")

# Load the graph from the GraphML file
@st.cache(allow_output_mutation=True)
def load_graph():
    # Read the GraphML file
    G = nx.read_graphml("sheep_ml.graphml.xml")
    
    # Convert node attribute "age" to integer
    for n, data in G.nodes(data=True):
        if "age" in data:
            try:
                data["age"] = int(data["age"])
            except ValueError:
                data["age"] = 0  # default/fallback value
        else:
            data["age"] = 0
    # Convert edge attribute "weight" to integer
    for u, v, data in G.edges(data=True):
        if "weight" in data:
            try:
                data["weight"] = int(data["weight"])
            except ValueError:
                data["weight"] = 1
        else:
            data["weight"] = 1
    return G

G = load_graph()

st.subheader("Graph Overview")
st.write(f"Number of nodes: {G.number_of_nodes()}")
st.write(f"Number of edges: {G.number_of_edges()}")

# Augment the graph: compute in-degree and out-degree for each node
in_degree = dict(G.in_degree())
out_degree = dict(G.out_degree())
nx.set_node_attributes(G, in_degree, "in_degree")
nx.set_node_attributes(G, out_degree, "out_degree")

# Create a Pyvis network for an interactive visualization
net = Network(height="600px", width="100%", directed=True, notebook=False)

# Transfer the NetworkX graph to Pyvis
net.from_nx(G)

# Enhance each node with tooltip info and adjust visual properties
for node in net.nodes:
    node_id = node["id"]
    # Retrieve node attributes; use "N/A" if missing
    age = G.nodes[node_id].get("age", "N/A")
    in_deg = G.nodes[node_id].get("in_degree", 0)
    out_deg = G.nodes[node_id].get("out_degree", 0)
    node["title"] = f"Sheep ID: {node_id}<br>Age: {age}<br>In-degree: {in_deg}<br>Out-degree: {out_deg}"
    # Scale node size by age (or use a default value)
    node["value"] = age if isinstance(age, int) else 10
    node["label"] = str(node_id)

# Customize visual options using Pyvis options (physics, labels, etc.)
net.set_options("""
var options = {
  "nodes": {
    "font": {
      "size": 16,
      "face": "Tahoma"
    },
    "scaling": {
      "min": 10,
      "max": 30
    }
  },
  "edges": {
    "arrows": {
      "to": {
        "enabled": true,
        "scaleFactor": 1
      }
    },
    "color": {
      "inherit": true
    },
    "smooth": false
  },
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -50,
      "centralGravity": 0.01,
      "springLength": 100,
      "springConstant": 0.08
    },
    "minVelocity": 0.75,
    "solver": "forceAtlas2Based"
  }
}
""")

# Save the network to an HTML file and embed it into the Streamlit app
net.save_graph("sheep_network.html")
with open("sheep_network.html", "r", encoding="utf-8") as f:
    html_content = f.read()

st.subheader("Interactive Network Visualization")
components.html(html_content, height=600, width="100%")

st.markdown("""
### Discussion and Findings

- **Expressiveness of the Visual Idiom:**  
  The node-link visualization clearly delineates each sheep as a node with directed edges indicating dominance interactions. Interactivity (zoom, pan, and hover tooltips) enables detailed exploration of the network.

- **Effectiveness of the Augmentation:**  
  Augmenting nodes with in-degree and out-degree metrics reveals the social hierarchy: nodes with high in-degree may indicate dominant sheep, while high out-degree might suggest a more subordinate role. Scaling nodes by age further highlights age-related trends in social status.

- **Observations:**  
  This interactive and augmented visualization facilitates both qualitative and quantitative insights into the dominance dynamics among bighorn sheep, identifying key individuals within the network.
""")
