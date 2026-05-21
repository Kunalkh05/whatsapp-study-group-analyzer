"""
Builds and calculates reply network structures between group members.
Visualizes the reply graph interactively using Pyvis, saving it locally.
"""

import tempfile
from pathlib import Path
from pyvis.network import Network

def detect_reply_chains(messages: list[dict], window: int = 3) -> list[dict]:
    """
    Detects reply links in the chronological stream of group messages.
    A reply is registered when B posts a message within a small index window
    immediately following B's predecessor A (where A and B are different senders).
    
    Args:
        messages (list[dict]): Chronologically sorted list of message dictionaries.
        window (int): The number of messages to look back to find the closest different sender.
        
    Returns:
        list[dict]: List of aggregated edge dictionaries: {"from_member": str, "to_member": str, "count": int}.
    """
    valid_msgs = [m for m in messages if not m.get("is_system") and not m.get("is_media")]
    
    edge_counts = {}
    
    for i in range(len(valid_msgs)):
        msg_b = valid_msgs[i]
        sender_b = msg_b.get("sender")
        if not sender_b or sender_b == "System":
            continue
            
        # Look backwards in the message list up to the window size
        for j in range(i - 1, max(-1, i - 1 - window), -1):
            msg_a = valid_msgs[j]
            sender_a = msg_a.get("sender")
            if not sender_a or sender_a == "System":
                continue
                
            # If the sender is different, we assume message B replied to message A
            if sender_a != sender_b:
                edge = (sender_b, sender_a)
                edge_counts[edge] = edge_counts.get(edge, 0) + 1
                break  # Stop search at the most recent different sender
                
    # Format to list of dicts
    edges = []
    for (from_member, to_member), count in edge_counts.items():
        edges.append({
            "from_member": from_member,
            "to_member": to_member,
            "count": count
        })
        
    return edges

def build_network_graph(edges: list[dict], member_scores: list[dict]) -> str:
    """
    Constructs an interactive, directed Pyvis Network.
    Node sizes map to Contributor Scores. Node colors map to labels (star, active, lurker).
    Edge thickness maps to reply frequency.
    Saves graph inside the local OS temp directory to keep application assets self-contained.
    
    Args:
        edges (list[dict]): Reply edges parsed from detect_reply_chains.
        member_scores (list[dict]): Ranked score dict list from score_all_members.
        
    Returns:
        str: Absolute file path to the saved interactive HTML graph page.
    """
    # Initialize Pyvis directed network with dark theme
    net = Network(
        directed=True,
        height="500px",
        width="100%",
        bgcolor="#1a1a1a",
        font_color="#ffffff"
    )
    
    # Store members to check existence before drawing connections
    nodes_added = set()
    
    for m in member_scores:
        name = m["member"]
        score = m["contributor_score"]
        label = m["label"]
        total_msgs = m["total_messages"]
        
        # Color palettes
        if label == "star":
            color = "#1D9E75"  # Green
        elif label == "active":
            color = "#EF9F27"  # Amber/Orange
        else:
            color = "#888780"  # Soft Gray
            
        # Scale node size for pleasant rendering
        node_size = int(15 + (score * 35))
        
        # Detail bubble
        hover_title = (
            f"<b>{name}</b><br>"
            f"Rank: {m['rank']}<br>"
            f"Score: {score:.4f}<br>"
            f"Role: {label.capitalize()}<br>"
            f"Total Messages: {total_msgs}"
        )
        
        net.add_node(
            name, 
            label=name, 
            size=node_size, 
            color=color, 
            title=hover_title,
            font={"color": "#ffffff", "size": 14}
        )
        nodes_added.add(name)
        
    # Draw directed edges
    for edge in edges:
        u = edge["from_member"]
        v = edge["to_member"]
        count = edge["count"]
        
        # Draw only if nodes exist in parsed subset
        if u in nodes_added and v in nodes_added:
            # Set scale for edge thickness
            thickness = min(10, max(1, int(count * 0.5)))
            edge_title = f"{u} replied to {v} {count} times"
            
            net.add_edge(
                u, 
                v, 
                value=thickness, 
                title=edge_title, 
                color="#555555",
                arrowStrikethrough=False
            )
            
    # Enable pleasant physics layout
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {"iterations": 150}
      }
    }
    """)
    
    # Save the output network to local temp directory
    temp_dir = tempfile.gettempdir()
    output_path = Path(temp_dir) / "group_ghost_network.html"
    
    net.save_graph(str(output_path))
    return str(output_path)

def get_most_replied_to(edges: list[dict]) -> list[tuple]:
    """
    Computes which group members are the most replied-to (highest indegree weighting).
    
    Args:
        edges (list[dict]): Reply edges list.
        
    Returns:
        list[tuple]: List of (member, incoming_reply_count) sorted descending.
    """
    replies_received = {}
    for edge in edges:
        to_m = edge["to_member"]
        count = edge["count"]
        replies_received[to_m] = replies_received.get(to_m, 0) + count
        
    return sorted(replies_received.items(), key=lambda x: x[1], reverse=True)

def get_most_replies_given(edges: list[dict]) -> list[tuple]:
    """
    Computes which group members are the most interactive (highest outdegree weighting).
    
    Args:
        edges (list[dict]): Reply edges list.
        
    Returns:
        list[tuple]: List of (member, outgoing_reply_count) sorted descending.
    """
    replies_sent = {}
    for edge in edges:
        from_m = edge["from_member"]
        count = edge["count"]
        replies_sent[from_m] = replies_sent.get(from_m, 0) + count
        
    return sorted(replies_sent.items(), key=lambda x: x[1], reverse=True)
