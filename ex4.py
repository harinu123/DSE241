import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.title("Bighorn Sheep Dominance Network Visualization")

st.markdown("""
This application visualizes the dominance interactions among female bighorn sheep.
Nodes represent individual sheep (with age data), and directed edges represent observed dominance interactions.
The visualization is augmented by computing the in‐degree and out‐degree for each node.
""")

# Load the data (ensure sheep_age.csv and sheep_edges.csv are in the same directory as this script)
@st.cache
def load_data():
    age_df = pd.read_csv("sheep_age.csv")
    edges_df = pd.read_csv("sheep_edges.csv")
    return age_df, edges_df

age_df, edges_df = load_data()

st.subheader("Sheep Age Data")
st.dataframe(age_df)

st.subheader("Sheep Edges Data")
st.dataframe(edges_df)

# Build the directed graph using NetworkX
G = nx.DiGraph()

# Add nodes with the age attribute
for _, row in age_df.iterrows():
    sheep_id = row["Sheep_ID"]
    age = row["Sheep_Age"]
    G.add_node(sheep_id, age=age)

# Add directed edges with weights
for _, row in edges_df.iterrows():
    src = row["Source_Sheep_ID"]
    tgt = row["Target_Sheep_ID"]
    weight = row["Weight"]
    G.add_edge(src, tgt, weight=weight)

# Augment the graph: compute in-degree and out-degree for each node
in_degree = dict(G.in_degree())
out_degree = dict(G.out_degree())
nx.set_node_attributes(G, in_degree, "in_degree")
nx.set_node_attributes(G, out_degree, "out_degree")

# Create a Pyvis network for an interactive visualization
net = Network(height="600px", width="100%", directed=True, notebook=False)

# Transfer the NetworkX graph to Pyvis
net.from_nx(G)

# Enhance each node with additional information and style options
for node in net.nodes:
    node_id = node["id"]
    age = G.nodes[node_id]["age"]
    in_deg = G.nodes[node_id]["in_degree"]
    out_deg = G.nodes[node_id]["out_degree"]
    # Set a tooltip with detailed info
    node["title"] = f"Sheep ID: {node_id}<br>Age: {age}<br>In-degree: {in_deg}<br>Out-degree: {out_deg}"
    # Use age to scale the node's value (which affects the displayed size)
    node["value"] = age  
    node["label"] = str(node_id)

# Customize physics and visual options with Pyvis
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

# Save and read the generated network graph HTML file
net.save_graph("sheep_network.html")
with open("sheep_network.html", "r", encoding="utf-8") as f:
    html_content = f.read()

st.subheader("Interactive Network Visualization")
components.html(html_content, height=600, width="100%")

st.markdown("""
### Discussion and Findings

- **Expressiveness of the Visual Idiom:**  
  The node-link visualization clearly represents each sheep as a node, with directed edges indicating the dominance relationships. By embedding the visualization in a web-based format (using Pyvis and Streamlit), users can interact with the network – zooming in/out and hovering over nodes to reveal details such as age and degree metrics.

- **Effectiveness of the Augmentation:**  
  Adding in-degree and out-degree metrics as part of the node tooltips provides insight into the social hierarchy; nodes with higher in-degree may be more dominant while high out-degree could indicate submissive behavior. Scaling node sizes by age further enriches the visualization, potentially revealing age-related trends in social dominance.

- **Observations:**  
  From the visualization, one can identify key individuals (nodes with larger size or higher connectivity) that play central roles in the social structure. This augmented and interactive display thus facilitates both qualitative and quantitative insights into the dominance dynamics among the bighorn sheep.
""")
