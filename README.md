# Dynamic-PathFinding-Agent
# AI Pathfinder — Informed Search with Dynamic Obstacles

A grid-based pathfinding visualizer built with **Python 3** and **Tkinter**. It implements two informed search algorithms — **Greedy Best-First Search** and **A\*** — with support for two heuristic functions, a fully interactive map editor, random map generation, and a **Dynamic Mode** that spawns obstacles in real time and replans the path automatically while the agent is in motion.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation & Running](#installation--running)
3. [Project Structure](#project-structure)
4. [How to Use](#how-to-use)
5. [Algorithms Explained](#algorithms-explained)
6. [Heuristic Functions](#heuristic-functions)
7. [Dynamic Mode](#dynamic-mode)
8. [GUI Features](#gui-features)
9. [Color Guide](#color-guide)
10. [Metrics Dashboard](#metrics-dashboard)
11. [Tips & Notes](#tips--notes)

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.7 or higher |
| Tkinter | Included with Python (no install needed) |

No third-party packages are required. The entire application runs on Python's standard library.

> **Linux users only:** Some Linux distributions do not bundle Tkinter with Python. Install it with:
> ```bash
> # Ubuntu / Debian
> sudo apt-get install python3-tk
>
> # Fedora
> sudo dnf install python3-tkinter
>
> # Arch Linux
> sudo pacman -S tk
> ```

---

## Installation & Running

### Step 1 — Check Python is installed
```bash
python --version
# or
python3 --version
```
You should see Python 3.7 or higher. If not, download from https://www.python.org/downloads/

### Step 2 — Run the application
```bash
python ai_pathfinder.py
```
or on some systems:
```bash
python3 ai_pathfinder.py
```

The GUI window will open immediately. No setup, no virtual environment, no pip install needed.

---

## Project Structure

```
ai_pathfinder/
├── ai_pathfinder.py      # Main application — run this file
└── README.md             # This file
```

The entire application is contained in a single Python file. All logic, GUI, and algorithms are self-contained.

---

## How to Use

### Step 1 — Set Up the Grid
- Click **Set Start Node**, then click any cell to place the start position (shown in purple)
- Click **Set Target Node**, then click any cell to place the goal (shown in dark blue)
- Click **Place/Remove Wall**, then click or drag across cells to toggle walls on and off

### Step 2 — Choose Grid Size (Optional)
- Enter your desired **Rows** and **Cols** values in the spinboxes at the top of the sidebar (range: 5 to 25)
- Click **Apply Grid Size** — the grid resizes and cell size auto-scales to fit the window without overflow

### Step 3 — Generate a Random Map (Optional)
- Adjust the **Density** slider to control how many walls are placed (0.10 = 10%, 0.60 = 60%)
- Click **Generate Random Map** to auto-fill the grid with random walls
- Note: this clears the start and target nodes — place them again after generating

### Step 4 — Select Algorithm and Heuristic
- Use the **Algorithm** dropdown to choose between Greedy Best-First Search and A\*
- Use the **Heuristic** dropdown to choose between Manhattan and Euclidean distance

### Step 5 — Run the Search
- Click **▶ Start Search** to begin
- Watch nodes being explored in real time (yellow = frontier, light blue = visited)
- The final path is highlighted in green when found
- Click **■ Stop Search** at any time to interrupt

---

## Algorithms Explained

### Greedy Best-First Search (GBFS)

GBFS uses only the heuristic value to decide which node to expand next. It always picks the node that **looks** closest to the goal, completely ignoring how far it has already travelled from the start.

```
f(n) = h(n)
```

- **Pros:** Very fast, expands few nodes, low memory usage
- **Cons:** Not guaranteed to find the shortest path; can get trapped in dead ends with walls
- **Best for:** Situations where speed matters more than path quality

### A* Search

A\* combines the actual travel cost from the start with the heuristic estimate to the goal. This gives it a balanced view of both how far it has come and how far it still needs to go.

```
f(n) = g(n) + h(n)

where:
  g(n) = actual cost from start to current node (number of steps taken)
  h(n) = heuristic estimate from current node to target
```

- **Pros:** Always finds the shortest (optimal) path; complete and reliable
- **Cons:** Slower than GBFS; explores more nodes; higher memory usage
- **Best for:** Situations where the shortest path is required

### Comparison Table

| Criterion | Greedy Best-First | A\* |
|---|---|---|
| Formula | f(n) = h(n) | f(n) = g(n) + h(n) |
| Optimal Path | No | Yes (guaranteed) |
| Complete | No | Yes |
| Speed | Very fast | Moderate |
| Nodes Visited | Fewer | More |
| Memory Usage | Low | Higher |
| Use Case | Speed-critical | Quality-critical |

---

## Heuristic Functions

### Manhattan Distance
```
h(n) = |row_current - row_target| + |col_current - col_target|
```
Counts the total horizontal and vertical distance between two cells. Best suited for grids where movement is restricted to up, down, left, and right (or 8-directional with uniform cost). This is the recommended heuristic for this application.

### Euclidean Distance
```
h(n) = sqrt((row_current - row_target)² + (col_current - col_target)²)
```
Measures the straight-line distance between two cells. More accurate for diagonal movement in continuous space. In grid environments with integer step costs, Manhattan typically performs better because it is a tighter lower bound.

Both heuristics are **admissible** — they never overestimate the true cost — which guarantees A\* will always find the optimal path.

---

## Dynamic Mode

Dynamic Mode simulates real-world navigation where the environment changes while the agent is moving.

### How to Enable
1. Check the **Enable Dynamic Obstacles** checkbox in the sidebar
2. Adjust the **Spawn Prob** slider to set how likely a new obstacle appears at each step (e.g. 0.10 = 10% chance per step)
3. Click **▶ Start Search**

### What Happens
1. The algorithm runs normally and computes the initial path (shown in green)
2. An **orange-red circle** (the agent) appears at the start and begins moving along the path step by step
3. At every step, there is a random chance a new black wall appears somewhere on the grid
4. If the new wall lands **on the current path**, the agent immediately stops and replans from its current position using the same algorithm
5. If the new wall is **off the current path**, the agent continues without any recalculation — no wasted computation
6. The agent keeps moving and replanning until it reaches the target or no path remains

### Re-planning Efficiency
- Replanning only triggers when necessary (obstacle is on the path)
- Replanning uses a fast silent version of the algorithm with no animation delay
- Only the green path is cleared and redrawn — walls and visited cells are preserved

---

## GUI Features

| Feature | Description |
|---|---|
| Set Start Node | Place the agent starting position (purple) |
| Set Target Node | Place the goal position (dark blue) |
| Place/Remove Wall | Click or drag to toggle walls on any cell |
| Clear Grid | Reset everything — removes all walls, start, and target |
| Apply Grid Size | Resize the grid from 5×5 up to 25×25; cell size auto-adjusts |
| Generate Random Map | Fill grid with random walls at user-defined density |
| Algorithm Dropdown | Choose Greedy Best-First Search or A\* |
| Heuristic Dropdown | Choose Manhattan or Euclidean distance |
| Enable Dynamic Obstacles | Toggle real-time obstacle spawning during agent movement |
| Spawn Prob Slider | Set probability of a new obstacle appearing each time step |
| Start Search | Run the selected algorithm with visualization |
| Stop Search | Interrupt the search at any point |
| Search Status | Displays current state: Ready, Searching, Re-planning, Path Found, No Path Found |

---

## Color Guide

| Color | Element | Description |
|---|---|---|
| Purple | Start Node | Agent starting position |
| Dark Blue | Target Node | Goal destination |
| Black | Wall | Impassable obstacle |
| Yellow | Frontier | Nodes currently in the priority queue (open list) |
| Light Blue | Visited / Explored | Nodes that have been expanded; number inside = visit order |
| Green | Path | Final computed route from start to target |
| Orange-Red circle | Agent | Current agent position during Dynamic Mode |

The **number** displayed inside each light blue cell shows the order in which that node was visited — 1 means it was the first node expanded, 2 was the second, and so on. This helps visualize how each algorithm explores the grid differently.

---

## Metrics Dashboard

After each search, three metrics are displayed at the bottom of the window:

| Metric | Description |
|---|---|
| Nodes Visited | Total number of nodes expanded (popped from the priority queue) during the search |
| Path Cost | Number of steps in the final path from start to target |
| Execution Time | Total time taken to compute the path, measured in milliseconds |

These metrics update in real time during the search and reset when a new search begins. Use them to compare the efficiency of GBFS vs A\* and Manhattan vs Euclidean across different grid configurations.

---

## Tips & Notes

- **A\* always finds the shortest path** — if you need the optimal route, always use A\*
- **GBFS is faster** — if you just need any valid path quickly, use Greedy Best-First
- **Manhattan heuristic is recommended** for this grid since movement cost is uniform (1 per step)
- **Higher spawn probability** in Dynamic Mode (e.g. 0.15–0.20) will trigger more frequent replanning and make the simulation more challenging
- **Larger grids** (e.g. 20×20) will show a clearer difference between GBFS and A\* in terms of nodes visited and path quality
- The grid **cell size automatically shrinks** as you increase the grid dimensions so the layout never breaks
- You can **click Stop Search** at any time without crashing — the grid state is preserved
