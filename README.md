# Ukraine Road Network – Dijkstra Pathfinding Visualizer
_A Python application for computing and visualizing the shortest paths between Ukrainian cities using Dijkstra’s algorithm._

## Overview
This project implements an interactive visualizer of Dijkstra’s shortest-path algorithm on a weighted graph representing the road network of Ukraine. Cities are modeled as graph vertices, highways as weighted edges (distances in km).  
The application provides a full graphical interface built with PySide6, allowing users to:
- inspect the national road graph,
- compute optimal routes,
- observe the algorithm’s execution step-by-step,
- dynamically edit the graph,
- visualize relaxations and the final path,
- measure execution time and path metrics.

## Key Features
### Shortest Path Search
- Classical Dijkstra algorithm with visual step recording.
- Early termination when the target is reached.
- Real-time visualization of active nodes, relaxations, visited sets, and reconstructed paths.

### Graph Editing Tools
- Add or remove cities.
- Add or remove roads.
- Convert undirected edges to directed arcs.
- Modify weights of existing edges.
- Immediate live refresh on the canvas.

### Interactive Visualization
- Map-based rendering of Ukraine.
- Cities drawn according to predefined coordinates.
- Dynamic highlighting of visited nodes, active edges, and final route.

### Search Controls
- Step-by-step execution.
- Automatic animation with adjustable delay.
- Pause and reset.
- Output of total distance and per-segment breakdown.

### Data Sources
- `distances.csv` – weighted edges between major Ukrainian cities.
- `cities_positions.json` – coordinates for visualization.

## Project Structure
```
ukraine_routes/
│   requirements.txt
│
├── app/
│   ├── main.py
│   ├── models/
│   │   data_loader.py
│   │   dijkstra.py
│   │   graph.py
│   ├── services/
│   │   graph_service.py
│   │   path_service.py
│   ├── ui/
│   │   controls_panel.py
│   │   graph_canvas.py
│   │   main_window.py
│   ├── resources/
│   │   dark_theme.qss
│   │   images/
│   │       ukraine_map.png
│
└── data/
    cities_positions.json
    distances.csv
```

## Installation
### 1. Clone the repository
```
git clone https://github.com/<your_username>/ukraine_routes.git
cd ukraine_routes
```
### 2. Create a virtual environment
```
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate    # Windows
```
### 3. Install dependencies
```
pip install -r requirements.txt
```

## Run the Application
```
python app/main.py
```

The interface will open showing the map of Ukraine, the graph canvas, and the control panel.

## How to Use the Program
### Selecting Start and Target Cities
Choose the source and destination in the control panel.

### Running Dijkstra
Click *Find Path* to start the algorithm and optionally use step mode.

### Viewing Results
The UI displays:
- the total distance,
- the full ordered list of cities,
- segment-by-segment distances,
- execution time.

### Editing the Graph
Use the panel to add/remove cities, add/remove roads, modify weights, or convert an undirected road into a directed arc.

## Algorithm Implementation
The search implementation is located in `dijkstra.py`.  
It provides:
- classical O(V²) Dijkstra,
- step recording for visualization,
- early stop on target,
- path reconstruction via predecessor tracking.

Each recorded step contains:
- current node,
- relaxed neighbor,
- updated distance (if improved),
- distance snapshot,
- visited nodes.

## License
MIT License.

