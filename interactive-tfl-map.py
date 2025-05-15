import networkx as nx
import pandas as pd
import folium

stations = pd.read_csv('Stations2018_Updated.csv', index_col='NAME')

G = nx.MultiDiGraph()

# List of category column names
lines = list(stations.columns[9:33])

# Add nodes with position attribute and line scores
for idx, row in stations.iterrows():
    node_attributes = {'pos': (row['x'], row['y'])}
    for line in lines:
        node_attributes[line] = row[line]
    G.add_node(row['OBJECTID'], **node_attributes)

# Acceptable score differences for undirected graphs (i.e. two-way routes, which are the vast majority)
u_tolerances = [1, 0.01, 0.0001, 0.000001]

# Acceptable score differences for directed graphs (i.e. one-way routes for Piccadilly at Heathrow T4 and Tram in Croydon)
d_tolerances = [100, 700, 1000, 5000, 10000, 10001]

# Iterate over all pairs of nodes
for i in G.nodes:
    for j in G.nodes:

        for line in lines:
            score_i = G.nodes[i].get(line)
            score_j = G.nodes[j].get(line)

            # Both nodes must have a valid score (not NaN)
            if pd.notna(score_i) and pd.notna(score_j):
                diff = abs(score_i - score_j)

            # Check if difference is exactly 1, 0.01, 0.001, 0.0001 or 0.00001 (within a small floating point tolerance)
                for u_tol in u_tolerances:
                    if abs(diff - u_tol) < 1e-9:
                        # Add edge if criteria met
                        G.add_edge(i, j, category=line, score_diff=diff, directed=False)

                for d_tol in d_tolerances:
                    if abs(diff - d_tol) < 1e-9:
                        # Add edge if criteria met
                        G.add_edge(i, j, category=line, score_diff=diff, directed=True)


pos = nx.get_node_attributes(G, 'pos')

m = folium.Map(location=[51.5081, -0.1248], zoom_start=12)

# Draw nodes
for index, row in stations.iterrows(): # Iterate through DataFrame rows to get OBJECTID and location
    node_id = row['OBJECTID']
    # Folium expects (latitude, longitude). The pos dictionary has (x, y) which are likely (longitude, latitude)
    # Need to swap x and y if x is longitude and y is latitude
    station_pos = (pos[node_id][1], pos[node_id][0]) # Swap (longitude, latitude) to (latitude, longitude) for Folium
    folium.CircleMarker(
        location=station_pos, # Use the specific location for the current node
        radius=6,
        color='black',
        fill=True,
        fill_color='black',
        popup=index # Use the station name for the popup
    ).add_to(m)

# Draw edges

edge_color_map = {
    'Bakerloo': '#b26300',
    'Central': '#dc241f',
    'Circle': '#ffd329',
    'District': '#007d32',
    'Hammersmith': '#f4a9be',
    'Jubilee': '#a1a5a7',
    'Metropolitan': '#9b0058',
    'Northern': '#000000',
    'Piccadilly': '#0019a8',
    'Victoria': '#0098d8',
    'Waterloo': '#93ceba',
    'Liberty': '#676767',
    'Lioness': '#f1b41c',
    'Mildmay': '#437ec1',
    'Suffragette': '#39b97a',
    'Weaver': '#972861',
    'Windrush': '#ef4d5e',
    'Beckton': '#53bfb4',
    'Woolwich': '#a9dddd',
    'Lewisham': '#255c4e',
    'Wimbeck': '#94ca4e',
    'Loop': '#204c24',
    'Elizabeth': '#6f4b9f'
}

for u, v, data in G.edges(data=True):
    draw_arrows = data.get('directed', False)
    category = data.get('category')

    edge_color = edge_color_map.get(category)

    if draw_arrows:
        # Get positions of source and target nodes
        x1, y1 = pos[u]
        x2, y2 = pos[v]

        # Get the line category for this edge
        line = data.get('category')

        # Get scores for the connected nodes
        score_u = G.nodes[u].get(line)
        score_v = G.nodes[v].get(line)

        # Check if both scores are valid
        if pd.notna(score_u) and pd.notna(score_v):
            # Determine the direction based on the stored score_diff
            # The score_diff for directed edges stores the actual difference (score_v - score_u)
            score_diff = data.get('score_diff')

            # If the stored score_diff is in the directed tolerances, draw a dashed arrow.
            if abs(score_diff) in [100, 700, 1000, 5000, 10000, 10001]: # Check absolute value against tolerances
                folium.PolyLine(
                    locations=[(y1, x1), (y2, x2)], # Use (lat, lon) format
                    color=edge_color,
                    weight=2,
                    opacity=0.7,
                    dash_array='5, 5' # Optional: make directed lines dashed
                ).add_to(m)


    else:
        # Draw undirected edges using Folium PolyLine
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        folium.PolyLine(
            locations=[(y1, x1), (y2, x2)], # Use (lat, lon) format
            color=edge_color,
            weight=2,
            opacity=0.7
        ).add_to(m)

m.save("tfl_lines_on_map.html")




