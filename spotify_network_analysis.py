# ========== IMPORTS ==========
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
from itertools import combinations
import numpy as np

# ========== LOAD COLLECTED DATA ==========
print("Loading your collected Spotify data...")
df = pd.read_csv("spotify_song_analysis.csv")  # Your CSV file

print(f"✅ Loaded {len(df)} tracks")

# ========== BUILD ARTIST COLLABORATION NETWORK ==========
print("\nBuilding artist collaboration network...")
G = nx.Graph()

# Process each song to find collaborations
for _, row in df.iterrows():
    # Get the list of artists for this song
    if pd.notna(row['artists_list']):
        # Convert string representation of list to actual list
        artists = eval(row['artists_list']) if isinstance(row['artists_list'], str) else row['artists_list']
    else:
        # Fallback: split the artist string
        artists = [a.strip() for a in row['artist'].split(",")]
    
    # Only create edges for actual collaborations (2+ artists on a song)
    if len(artists) >= 2:
        for a1, a2 in combinations(artists, 2):
            if G.has_edge(a1, a2):
                G[a1][a2]["weight"] += 1
                G[a1][a2]["songs"].append(row['song_name'])
            else:
                G.add_edge(a1, a2, weight=1, songs=[row['song_name']])

print(f"- Network has {len(G.nodes())} artists and {len(G.edges())} collaborations")

# ========== CALCULATE IMPORTANCE METRICS ==========
print("\nCalculating artist importance metrics...")

# Count how many songs each artist appears on
artist_mentions = Counter()
for _, row in df.iterrows():
    if pd.notna(row['artists_list']):
        artists = eval(row['artists_list']) if isinstance(row['artists_list'], str) else row['artists_list']
    else:
        artists = [a.strip() for a in row['artist'].split(",")]
    artist_mentions.update(artists)

nx.set_node_attributes(G, artist_mentions, "song_count")

# Calculate centrality measures
betweenness = nx.betweenness_centrality(G, weight='weight')
degree_centrality = nx.degree_centrality(G)

nx.set_node_attributes(G, betweenness, "betweenness")
nx.set_node_attributes(G, degree_centrality, "degree_centrality")

# ========== IDENTIFY IMPORTANT NODES ==========
print("\nTOP 10 MOST IMPORTANT ARTISTS")
print("="*60)

print("\n  BY BETWEENNESS CENTRALITY (Network Bridges):")
print("-" * 50)
top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
for i, (artist, score) in enumerate(top_betweenness, 1):
    song_count = artist_mentions.get(artist, 0)
    collaborators = len(list(G.neighbors(artist)))
    print(f"{i:2d}. {artist:25} | Centrality: {score:.4f} | Songs: {song_count:2d} | Collaborators: {collaborators:2d}")

# ========== VISUALIZATION 1: NETWORK ==========
print("\nCreating network visualization with ALL nodes labeled...")

pos = nx.spring_layout(G, seed=42, k=8, iterations=1200)  # Increase k from 3 to 5
fig1 = plt.figure(figsize=(16, 12))  # Increase from (20, 16)
node_sizes = [max(G.nodes[n]["song_count"] * 400, 800) for n in G.nodes()]
node_colors = [G.nodes[n]["betweenness"] for n in G.nodes()]

# Draw the network
nx.draw_networkx_edges(G, pos, alpha=0.8, edge_color='black', width=1.5)
nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                             node_color=node_colors, cmap="plasma", 
                             alpha=0.9, edgecolors='black', linewidths=2)  # More opaque, thicker borders

labels = {artist: artist for artist in G.nodes()}
nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", 
                                alpha=0.7, edgecolor='black', linewidth=0.5))

print(f"   ✅ Labeled ALL {len(labels)} artists")

plt.colorbar(nodes, label="Betweenness Centrality\n(How much they connect different parts of the network)")
plt.title("Spotify Artist Collaboration Network - ALL ARTISTS LABELED\n"
          "• Node size = Number of songs featuring the artist\n"
          "• Node color = Network importance (betweenness centrality)\n"
          "• Edges = Collaborations between artists", 
          fontsize=16, fontweight='bold', pad=20)
plt.axis("off")

plt.tight_layout()
plt.savefig('artist_collaboration_network_nodes.png', dpi=300, bbox_inches='tight', facecolor='white')

# ========== VISUALIZATION 2: SCATTER PLOT ==========
print("Creating Visualization 2: Centrality Comparison Scatter Plot...")
fig2 = plt.figure(figsize=(10, 6))

# Get data for scatter plot
artists = []
degree_scores = []
betweenness_scores = []
song_counts = []

for artist in G.nodes():
    artists.append(artist)
    degree_scores.append(G.nodes[artist]['degree_centrality'])
    betweenness_scores.append(G.nodes[artist]['betweenness'])
    song_counts.append(G.nodes[artist]['song_count'])


scatter = plt.scatter(degree_scores, betweenness_scores, 
                     c=betweenness_scores, cmap='viridis', 
                     s=np.array(song_counts)*50, alpha=0.7)


for artist, deg, bet in zip(artists, degree_scores, betweenness_scores):
    plt.annotate(artist, (deg, bet), 
                xytext=(10, 10), 
                textcoords='offset points',
                fontsize=6, 
                alpha=0.8,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6, linewidth=0.5),
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor='none'))

plt.xlabel('Degree Centrality (Number of Collaborators)')
plt.ylabel('Betweenness Centrality (Bridge Importance)')
plt.title('Artist Importance: Collaboration vs Bridge Roles\n(Size = Number of Songs)')
plt.colorbar(scatter, label='Betweenness Centrality')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('centrality_scatter_plot.png', dpi=300, bbox_inches='tight')

# ========== VISUALIZATION 3: Top Artists Bar Charts ==========
print("Creating Visualization 3: Top Artists Bar Charts...")
fig3, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Top betweenness artists
top_betweenness_artists = [artist for artist, _ in top_betweenness[:10]]
top_betweenness_scores = [betweenness[artist] for artist in top_betweenness_artists]

bars1 = ax1.barh(range(len(top_betweenness_artists)), top_betweenness_scores, 
                color='skyblue', alpha=0.7)
ax1.set_yticks(range(len(top_betweenness_artists)))
ax1.set_yticklabels(top_betweenness_artists, fontsize=10)
ax1.set_xlabel('Betweenness Centrality Score')
ax1.set_title('Top 10 Bridge Artists\n(Connect Different Parts of the Network)')
ax1.invert_yaxis()

# Add value labels
for i, bar in enumerate(bars1):
    width = bar.get_width()
    ax1.text(width + 0.001, bar.get_y() + bar.get_height()/2, 
            f'{width:.4f}', ha='left', va='center', fontsize=9)

# Top degree centrality artists
top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_degree_artists = [artist for artist, _ in top_degree]
top_degree_scores = [score for _, score in top_degree]

bars2 = ax2.barh(range(len(top_degree_artists)), top_degree_scores, 
                color='lightcoral', alpha=0.7)
ax2.set_yticks(range(len(top_degree_artists)))
ax2.set_yticklabels(top_degree_artists, fontsize=10)
ax2.set_xlabel('Degree Centrality Score')
ax2.set_title('Top 10 Most Collaborative Artists\n(Most Diverse Collaboration Portfolio)')
ax2.invert_yaxis()

# Add value labels
for i, bar in enumerate(bars2):
    width = bar.get_width()
    ax2.text(width + 0.001, bar.get_y() + bar.get_height()/2, 
            f'{width:.4f}', ha='left', va='center', fontsize=9)

plt.tight_layout()
plt.savefig('top_artists_bar_charts.png', dpi=300, bbox_inches='tight')

print(f"\nSaved additional visualizations:")
print(f"   ✅ centrality_scatter_plot.png")
print(f"   ✅ top_artists_bar_charts.png")

print("\ALL VISUALIZATIONS COMPLETED!")

# ========== SAVE NETWORK DATA ==========
print("\n  Saving network analysis results...")

# Save artist importance metrics
network_data = []
for artist in G.nodes():
    network_data.append({
        'artist': artist,
        'song_count': G.nodes[artist]['song_count'],
        'betweenness_centrality': G.nodes[artist]['betweenness'],
        'degree_centrality': G.nodes[artist]['degree_centrality'],
        'number_of_collaborators': len(list(G.neighbors(artist)))
    })

network_df = pd.DataFrame(network_data)
network_df = network_df.sort_values('betweenness_centrality', ascending=False)
network_df.to_csv("artist_network_analysis.csv", index=False)

print(f"   ✅ artist_network_analysis.csv - {len(network_df)} artists with importance metrics")

# ========== FINDINGS ==========
print("\n" + "="*70)
print("  EXTRA INFO")
print("="*70)

print(f"\n  FINDING:")
print(f"   1. {top_betweenness[0][0]} is the MOST IMPORTANT CONNECTOR")
print(f"      • Betweenness centrality: {top_betweenness[0][1]:.4f}")
print(f"      • Appears in {artist_mentions[top_betweenness[0][0]]} songs")
print(f"      • Collaborates with {len(list(G.neighbors(top_betweenness[0][0])))} artists")

print(f"\n   2. Network Statistics:")
print(f"      • {len(G.nodes())} total artists analyzed")
print(f"      • {len(G.edges())} collaboration relationships")
print(f"      • {len(df)} songs from popular playlists")

