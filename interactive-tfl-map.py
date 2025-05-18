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

# The following shows acceptable score differences for undirected graphs (i.e. two-way routes, which are the vast majority).

u_tolerances = [1, 0.01, 0.0001, 0.000001]

# Within a line, any pair of stations with score diff of 1 are adjacent to each other. 

# If there are n additional branches of the line that branch out from one station, then the score diffs 
# on one branch will be 1/100, then 1/(100^2) on another, all the way up to score diffs of 1/(100^n).

# On the TfL network, there are a maximum of 3 additional branches from one station (Earl's Court on the District line);
# you have the main 'stem' going to Upminster, and then the branches to Wimbledon, Edgware Road and Kensington Olympia.
# Therefore, the acceptable score differences go up to 1/(100^3).

# I've used 1/100, because if 1/10 was used instead, the scores would seep into the unit digits if there are more than 
# 9 stations in a branch (e.g. scores would be 5.1, 5.2, 5.3, ... 6, 6.1), which can be the case on the TfL network.
# The computer will think that the station with a score of 6, will be adjacent to station with a score of 5 
# (6-5 gives a score diff of 1, which is a signal for edge creation), which is most likely not going to be the case. 
# The same goes for stations with score differences 5.1 and 6.1, 5.2 and 6.2, etc.

# For instance, if Camden Town had a score of 10, Kentish Town would have a score of 10.1, and then going along the
# whole branch, High Barnet would have a score of 11. This would imply that Camden Town is adjacent to High Barnet.

# 1/100 has been chosen as there are no branches with 100 stations, so the above phenomenon wouldn't occur.

# The following shows acceptable score differences for directed graphs (i.e. one-way routes for Piccadilly at 
# Heathrow T4 and Tramlink in Croydon)

d_tolerances = [100, 700, 1000, 5000, 10000, 10001]

# To distinguish stations on one-way routes, I've gone the other way and have initially used 100 as a score diff for the 
# one-way system on the Wimbeck line in Croydon.

# However, I needed to create an edge between Church Street (with a score of 713) and Wandle Park (with a score of 13),
# so I had to include 700 as an acceptable score diff.

# I initially tried to use the score diff of 100 again for the one-way system on the Loop line in Croydon, but as there
# are 5 stops on this loop, I would need to use 500 as an acceptable score diff, which would also create an edge between 
# Wandle Park and East Croydon (with scores 13 and 513 respectively), which doesn't exist on the network.

# There are no one-way routes with more than 10 stops, so I was able to use 1000 as score diff for that one-way
# system on the Loop line in Croydon, and then 10000 for the one-way system in Heathrow.

# The 5000 connects Wellesley Road with East Croydon on the Loop line, and the 10001 connects Heathrow T4 with
# Heathrow T123 on the Piccadilly line. 

# Iterate over all pairs of nodes
for i in G.nodes:
    for j in G.nodes:

        for line in lines:
            score_i = G.nodes[i].get(line)
            score_j = G.nodes[j].get(line)

            # Both nodes must have a valid score (not NaN)
            if pd.notna(score_i) and pd.notna(score_j):
                diff = abs(score_i - score_j)

            # Check if difference is exactly 1, 0.01, 0.0001 or 0.000001 (within a small floating point tolerance)
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

    passenger_count = row['Weekly passenger count 2024']
    if pd.isna(passenger_count):
        passenger_count_display = "--"
    else:
        # Format the integer with commas
        passenger_count_display = f"{int(passenger_count):,}"

    popup_html = f"""
    <div style="width: 200px; height: 100px;">
        <b>Station:</b> {index}<br><br>
        <b>Lines:</b> {row['NETWORK']}<br><br>
        <b>Weekly passenger count 2024:</b> {passenger_count_display}
    </div>
    """
    
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

            # If the stored score_diff is in the directed tolerances, draw a dashed line.
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




