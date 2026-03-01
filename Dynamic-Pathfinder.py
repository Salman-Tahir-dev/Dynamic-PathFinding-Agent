import tkinter as tk
from tkinter import messagebox, ttk
import time
import heapq
import random
import math
# # v1.0 - Initial release, commit it
# --- Constants ---
DEFAULT_ROWS = 10
DEFAULT_COLS = 10
CELL_SIZE = 50       # default, recalculated dynamically
DELAY = 0.05

# Max canvas area (leaves room for sidebar ~220px)
MAX_CANVAS_W = 900
MAX_CANVAS_H = 620

def calc_cell_size(rows, cols):
    """Return the largest square cell size that keeps grid within MAX bounds."""
    size_w = MAX_CANVAS_W // cols
    size_h = MAX_CANVAS_H // rows
    return max(10, min(size_w, size_h, 50))  # clamp between 10 and 50

# Colors
EMPTY_COLOR = "white"
WALL_COLOR = "black"
START_COLOR = "#740074"
TARGET_COLOR = "#0D048B"
FRONTIER_COLOR = "yellow"
EXPLORED_COLOR = "#ADD8E6"
PATH_COLOR = "#00C800"
SIDEBAR_BG = "#f0f0f0"
BUTTON_TEXT_COLOR = "white"
LABEL_COLOR = "#2196F3"

MOVES = [
    (-1, 0), (0, 1), (1, 0), (0, -1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]


# --- Node Class ---
class Node:
    def __init__(self, r, c, parent=None, g=0, h=0):
        self.r = r
        self.c = c
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other):
        return self.f < other.f


# --- Cell Class ---
class Cell:
    def __init__(self, row, col, canvas_id):
        self.row = row
        self.col = col
        self.canvas_id = canvas_id
        self.type = "empty"


# --- Main App ---
class GridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Pathfinder - Informed Search")

        self.rows = DEFAULT_ROWS
        self.cols = DEFAULT_COLS
        self.cell_size = calc_cell_size(DEFAULT_ROWS, DEFAULT_COLS)
        self.mode = "wall"
        self.start_pos = None
        self.target_pos = None
        self.grid = []
        self.algorithm = tk.StringVar(value="A*")
        self.heuristic = tk.StringVar(value="Manhattan")
        self.obstacle_density = tk.DoubleVar(value=0.3)
        self.dynamic_mode = tk.BooleanVar(value=False)
        self.dynamic_prob = tk.DoubleVar(value=0.05)
        self.stop_flag = False
        self.visit_count = 0
        self.path_cost = 0
        self.exec_time = 0
        self.current_path = []
        self.node_visit_map = {}

        # Rows/Cols input vars
        self.rows_var = tk.IntVar(value=DEFAULT_ROWS)
        self.cols_var = tk.IntVar(value=DEFAULT_COLS)

        self._build_ui()
        self.create_grid()

    def _build_ui(self):
        # ── Root layout: top area (grid + sidebar) and bottom bar ──
        main_frame = tk.Frame(self.root, bg=SIDEBAR_BG)
        main_frame.pack(fill="both", expand=True)

        # ── TOP: grid on left, sidebar on right ──
        top_frame = tk.Frame(main_frame, bg=SIDEBAR_BG)
        top_frame.pack(fill="both", expand=True)

        # Canvas
        canvas_frame = tk.Frame(top_frame, bg="white", relief="solid", bd=1)
        canvas_frame.pack(side="left", padx=10, pady=10, anchor="n")

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            bg="white", highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.cell_clicked)
        self.canvas.bind("<B1-Motion>", self.cell_clicked)

        # ── Scrollable Sidebar (right) ──
        sidebar_h = DEFAULT_ROWS * self.cell_size
        sidebar_container = tk.Frame(top_frame, bg=SIDEBAR_BG, width=210, height=sidebar_h)
        sidebar_container.pack(side="left", fill="y", padx=(0, 10), pady=10, anchor="n")
        sidebar_container.pack_propagate(False)
        self.sidebar_container = sidebar_container

        sb_canvas = tk.Canvas(sidebar_container, bg=SIDEBAR_BG, highlightthickness=0, width=193)
        sb_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(sidebar_container, orient="vertical", command=sb_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        sb_canvas.configure(yscrollcommand=scrollbar.set)

        sidebar = tk.Frame(sb_canvas, bg=SIDEBAR_BG)
        sidebar_window = sb_canvas.create_window((0, 0), window=sidebar, anchor="nw")

        def _on_frame_configure(event):
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all"))

        def _on_canvas_configure(event):
            sb_canvas.itemconfig(sidebar_window, width=event.width)

        sidebar.bind("<Configure>", _on_frame_configure)
        sb_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        sb_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ── Sidebar helpers ──
        def section(text):
            tk.Label(sidebar, text=text, bg=SIDEBAR_BG,
                     font=("Arial", 9, "bold"), fg="#333").pack(pady=(8, 2), anchor="w", padx=5)

        def btn(parent, text, color, cmd):
            tk.Button(parent, text=text, bg=color, fg=BUTTON_TEXT_COLOR,
                      font=("Arial", 9), command=cmd, relief="flat",
                      activebackground=color).pack(fill="x", pady=2, padx=5)

        # Grid size
        section("Grid Size:")
        size_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        size_frame.pack(fill="x", padx=5)
        tk.Label(size_frame, text="Rows:", bg=SIDEBAR_BG, font=("Arial", 8)).grid(row=0, column=0, sticky="w")
        tk.Spinbox(size_frame, from_=5, to=25, textvariable=self.rows_var, width=4,
                   font=("Arial", 8)).grid(row=0, column=1, padx=2)
        tk.Label(size_frame, text="Cols:", bg=SIDEBAR_BG, font=("Arial", 8)).grid(row=0, column=2, sticky="w")
        tk.Spinbox(size_frame, from_=5, to=25, textvariable=self.cols_var, width=4,
                   font=("Arial", 8)).grid(row=0, column=3, padx=2)
        btn(sidebar, "Apply Grid Size", "#607D8B", self.apply_grid_size)

        # Node Controls
        section("Node Controls:")
        btn(sidebar, "Set Start Node", "#740074", lambda: self.set_mode("start"))
        btn(sidebar, "Set Target Node", "#0D048B", lambda: self.set_mode("target"))
        btn(sidebar, "Place/Remove Wall", "#000000", lambda: self.set_mode("wall"))
        btn(sidebar, "Clear Grid", "#E21616", self.clear_grid)

        # Random Map
        section("Random Map:")
        density_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        density_frame.pack(fill="x", padx=5)
        tk.Label(density_frame, text="Density:", bg=SIDEBAR_BG, font=("Arial", 8)).pack(side="left")
        tk.Scale(density_frame, from_=0.1, to=0.6, resolution=0.05,
                 variable=self.obstacle_density, orient="horizontal",
                 bg=SIDEBAR_BG, length=110, font=("Arial", 7)).pack(side="left")
        btn(sidebar, "Generate Random Map", "#795548", self.generate_random_map)

        # Algorithm
        section("Algorithm:")
        self.algo_menu = ttk.Combobox(sidebar, textvariable=self.algorithm, state="readonly",
                                       font=("Arial", 9))
        self.algo_menu['values'] = ("Greedy Best-First", "A*")
        self.algo_menu.pack(fill="x", padx=5, pady=2)

        section("Heuristic:")
        self.heuristic_menu = ttk.Combobox(sidebar, textvariable=self.heuristic, state="readonly",
                                            font=("Arial", 9))
        self.heuristic_menu['values'] = ("Manhattan", "Euclidean")
        self.heuristic_menu.pack(fill="x", padx=5, pady=2)

        # Dynamic Mode
        section("Dynamic Mode:")
        dyn_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        dyn_frame.pack(fill="x", padx=5)
        tk.Checkbutton(dyn_frame, text="Enable Dynamic Obstacles",
                       variable=self.dynamic_mode, bg=SIDEBAR_BG,
                       font=("Arial", 8)).pack(anchor="w")
        prob_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        prob_frame.pack(fill="x", padx=5)
        tk.Label(prob_frame, text="Spawn Prob:", bg=SIDEBAR_BG, font=("Arial", 8)).pack(side="left")
        tk.Scale(prob_frame, from_=0.01, to=0.2, resolution=0.01,
                 variable=self.dynamic_prob, orient="horizontal",
                 bg=SIDEBAR_BG, length=100, font=("Arial", 7)).pack(side="left")

        # Search Buttons
        tk.Frame(sidebar, height=5, bg=SIDEBAR_BG).pack()
        btn(sidebar, "▶  Start Search", "#f44336", self.start_search)
        btn(sidebar, "■  Stop Search", "#FF9800", self.stop_search)

        # Status
        section("Search Status:")
        self.status_lbl = tk.Label(sidebar, text="Ready", bg="white", fg="black",
                                    relief="sunken", font=("Arial", 9), width=18)
        self.status_lbl.pack(pady=3, padx=5, fill="x")

        # ── BOTTOM BAR: Metrics + Legend side by side ──
        bottom_bar = tk.Frame(main_frame, bg="#e0e0e0", relief="groove", bd=1)
        bottom_bar.pack(fill="x", padx=10, pady=(0, 8))

        # -- Metrics section (left) --
        metrics_section = tk.Frame(bottom_bar, bg="#e0e0e0")
        metrics_section.pack(side="left", padx=15, pady=6)

        tk.Label(metrics_section, text="📊  Metrics", bg="#e0e0e0",
                 font=("Arial", 9, "bold"), fg="#333").pack(anchor="w")

        metrics_inner = tk.Frame(metrics_section, bg="white", relief="sunken", bd=1)
        metrics_inner.pack(anchor="w", pady=(2, 0))

        self.nodes_lbl = tk.Label(metrics_inner, text="Nodes Visited:  0",
                                   bg="white", font=("Arial", 9), padx=10, pady=2)
        self.nodes_lbl.grid(row=0, column=0, sticky="w")

        tk.Frame(metrics_inner, bg="#ccc", width=1).grid(row=0, column=1, sticky="ns", padx=4)

        self.cost_lbl = tk.Label(metrics_inner, text="Path Cost:  0",
                                  bg="white", font=("Arial", 9), padx=10, pady=2)
        self.cost_lbl.grid(row=0, column=2, sticky="w")

        tk.Frame(metrics_inner, bg="#ccc", width=1).grid(row=0, column=3, sticky="ns", padx=4)

        self.time_lbl = tk.Label(metrics_inner, text="Exec Time:  0 ms",
                                  bg="white", font=("Arial", 9), padx=10, pady=2)
        self.time_lbl.grid(row=0, column=4, sticky="w")

        # Vertical divider
        tk.Frame(bottom_bar, bg="#bbb", width=1).pack(side="left", fill="y", pady=4, padx=5)

        # -- Legend section (right) --
        legend_section = tk.Frame(bottom_bar, bg="#e0e0e0")
        legend_section.pack(side="left", padx=10, pady=6)

        tk.Label(legend_section, text="🗺  Legend", bg="#e0e0e0",
                 font=("Arial", 9, "bold"), fg="#333").pack(anchor="w")

        legend_inner = tk.Frame(legend_section, bg="#e0e0e0")
        legend_inner.pack(anchor="w", pady=(2, 0))

        legends = [
            (START_COLOR, "Start"), (TARGET_COLOR, "Target"), (WALL_COLOR, "Wall"),
            (FRONTIER_COLOR, "Frontier"), (EXPLORED_COLOR, "Visited"), (PATH_COLOR, "Path")
        ]
        for i, (color, label) in enumerate(legends):
            item = tk.Frame(legend_inner, bg="#e0e0e0")
            item.grid(row=0, column=i, padx=6)
            tk.Label(item, bg=color, width=3, height=1,
                     relief="solid", bd=1).pack(side="left", padx=(0, 3))
            tk.Label(item, text=label, bg="#e0e0e0",
                     font=("Arial", 8)).pack(side="left")

    def set_status(self, text, color="black"):
        self.status_lbl.config(text=text, fg=color)

    def update_metrics(self):
        self.nodes_lbl.config(text=f"Nodes Visited: {self.visit_count}")
        self.cost_lbl.config(text=f"Path Cost: {self.path_cost}")
        self.time_lbl.config(text=f"Exec Time: {self.exec_time:.1f} ms")

    def apply_grid_size(self):
        self.rows = self.rows_var.get()
        self.cols = self.cols_var.get()
        self.cell_size = calc_cell_size(self.rows, self.cols)
        self.start_pos = None
        self.target_pos = None
        self.grid = []
        new_w = self.cols * self.cell_size
        new_h = self.rows * self.cell_size
        self.canvas.config(width=new_w, height=new_h)
        self.canvas.delete("all")
        self.sidebar_container.config(height=new_h)
        self.create_grid()
        self.root.geometry("")

    def create_grid(self):
        self.grid = []
        cs = self.cell_size
        for row in range(self.rows):
            row_cells = []
            for col in range(self.cols):
                x1 = col * cs
                y1 = row * cs
                x2 = x1 + cs
                y2 = y1 + cs
                rect = self.canvas.create_rectangle(x1, y1, x2, y2,
                                                     fill=EMPTY_COLOR, outline="gray")
                row_cells.append(Cell(row, col, rect))
            self.grid.append(row_cells)

    def set_mode(self, mode):
        self.mode = mode

    def cell_clicked(self, event):
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return
        cell = self.grid[row][col]
        if self.mode == "start":
            if self.start_pos:
                self.update_cell_type(self.start_pos[0], self.start_pos[1], "empty")
            self.start_pos = (row, col)
            self.update_cell_type(row, col, "start")
        elif self.mode == "target":
            if self.target_pos:
                self.update_cell_type(self.target_pos[0], self.target_pos[1], "empty")
            self.target_pos = (row, col)
            self.update_cell_type(row, col, "target")
        elif self.mode == "wall":
            if (row, col) not in (self.start_pos, self.target_pos):
                new_type = "empty" if cell.type == "wall" else "wall"
                self.update_cell_type(row, col, new_type)

    def update_cell_type(self, r, c, type_name):
        self.grid[r][c].type = type_name
        self.update_cell_color(r, c)

    def update_cell_color(self, row, col, number=None):
        cell = self.grid[row][col]
        colors = {
            "empty": EMPTY_COLOR,
            "wall": WALL_COLOR,
            "start": START_COLOR,
            "target": TARGET_COLOR,
            "explored": EXPLORED_COLOR,
            "frontier": FRONTIER_COLOR,
            "path": PATH_COLOR,
        }
        color = colors.get(cell.type, EMPTY_COLOR)
        self.canvas.itemconfig(cell.canvas_id, fill=color)
        # Remove old text
        self.canvas.delete(f"txt_{row}_{col}")
        if number is not None:
            cs = self.cell_size
            self.canvas.create_text(
                col * cs + cs // 2,
                row * cs + cs // 2,
                text=str(number), fill="black",
                font=("Arial", max(6, cs // 6)),
                tags=f"txt_{row}_{col}"
            )

    def get_neighbors(self, r, c):
        neighbors = []
        for dr, dc in MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc].type not in ("wall",):
                    neighbors.append((nr, nc))
        return neighbors

    def heuristic_value(self, r, c):
        tr, tc = self.target_pos
        if self.heuristic.get() == "Manhattan":
            return abs(r - tr) + abs(c - tc)
        else:  # Euclidean
            return math.sqrt((r - tr) ** 2 + (c - tc) ** 2)

    def animate_frontier(self, r, c):
        if self.stop_flag:
            raise StopIteration
        cell = self.grid[r][c]
        if (r, c) != self.start_pos and (r, c) != self.target_pos:
            cell.type = "frontier"
            self.update_cell_color(r, c)
        self.root.update()

    def animate_explored(self, r, c):
        if self.stop_flag:
            raise StopIteration
        cell = self.grid[r][c]
        if (r, c) != self.start_pos and (r, c) != self.target_pos:
            cell.type = "explored"
            self.visit_count += 1
            self.node_visit_map[(r, c)] = self.visit_count
            self.update_cell_color(r, c, number=self.visit_count)
            self.update_metrics()
        self.root.update()
        time.sleep(DELAY)

    def clear_grid(self):
        self.start_pos = None
        self.target_pos = None
        self.stop_flag = True
        self.node_visit_map = {}
        self.current_path = []
        self.visit_count = 0
        self.path_cost = 0
        self.exec_time = 0
        self.set_status("Ready")
        self.update_metrics()
        for row in self.grid:
            for cell in row:
                cell.type = "empty"
                self.update_cell_color(cell.row, cell.col)

    def clear_path_only(self):
        self.visit_count = 0
        self.path_cost = 0
        self.node_visit_map = {}
        self.current_path = []
        for row in self.grid:
            for cell in row:
                if cell.type in ("explored", "frontier", "path"):
                    cell.type = "empty"
                    self.update_cell_color(cell.row, cell.col)

    def stop_search(self):
        self.stop_flag = True
        self.set_status("Stopped", "red")

    def generate_random_map(self):
        self.clear_grid()
        density = self.obstacle_density.get()
        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) not in (self.start_pos, self.target_pos):
                    if random.random() < density:
                        self.update_cell_type(row, col, "wall")

    def reconstruct_path(self, node):
        path = []
        curr = node
        while curr:
            path.append((curr.r, curr.c))
            curr = curr.parent
        path.reverse()
        self.current_path = path
        self.path_cost = len(path) - 1
        for r, c in path:
            if (r, c) != self.start_pos and (r, c) != self.target_pos:
                self.grid[r][c].type = "path"
                num = self.node_visit_map.get((r, c))
                self.update_cell_color(r, c, number=num)
                self.root.update()
                time.sleep(DELAY)
        self.update_metrics()
        return path

    def path_blocked(self):
        """Check if any cell ahead in current_path is now a wall."""
        for r, c in self.current_path:
            if (r, c) == self.start_pos or (r, c) == self.target_pos:
                continue
            if self.grid[r][c].type == "wall":
                return True
        return False

    def spawn_one_obstacle(self):
        """
        Unconditionally place one wall on a random non-special cell.
        Returns (r, c) placed or None if no valid cell found.
        """
        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) == self.start_pos or (r, c) == self.target_pos:
                    continue
                if self.grid[r][c].type != "wall":
                    candidates.append((r, c))
        if not candidates:
            return None
        r, c = random.choice(candidates)
        self.grid[r][c].type = "wall"
        self.canvas.itemconfig(self.grid[r][c].canvas_id, fill=WALL_COLOR)
        self.canvas.delete(f"txt_{r}_{c}")
        return (r, c)

    # --- Non-animated search (used during dynamic replanning) ---
    def _search_silent(self, algo, start):
        """Run search WITHOUT animation - used for fast replanning during dynamic mode."""
        if algo == "Greedy Best-First":
            return self._gbfs_silent(start)
        else:
            return self._astar_silent(start)

    def _gbfs_silent(self, start):
        h = self.heuristic_value(start[0], start[1])
        start_node = Node(*start, h=h)
        open_list = [(h, id(start_node), start_node)]
        visited = {start}
        while open_list:
            _, _, curr = heapq.heappop(open_list)
            if (curr.r, curr.c) == self.target_pos:
                return curr
            for nr, nc in self.get_neighbors(curr.r, curr.c):
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    h = self.heuristic_value(nr, nc)
                    neighbor = Node(nr, nc, curr, h=h)
                    neighbor.f = h
                    heapq.heappush(open_list, (h, id(neighbor), neighbor))
        return None

    def _astar_silent(self, start):
        h = self.heuristic_value(start[0], start[1])
        start_node = Node(*start, g=0, h=h)
        open_list = [(start_node.f, id(start_node), start_node)]
        visited = {}
        while open_list:
            _, _, curr = heapq.heappop(open_list)
            pos = (curr.r, curr.c)
            if pos == self.target_pos:
                return curr
            if pos in visited and visited[pos] <= curr.g:
                continue
            visited[pos] = curr.g
            for nr, nc in self.get_neighbors(curr.r, curr.c):
                new_g = curr.g + 1
                if (nr, nc) not in visited or visited.get((nr, nc), float('inf')) > new_g:
                    h = self.heuristic_value(nr, nc)
                    neighbor = Node(nr, nc, curr, g=new_g, h=h)
                    heapq.heappush(open_list, (neighbor.f, id(neighbor), neighbor))
        return None

    def _draw_path_silent(self, node):
        """Draw path on canvas from a node without animation."""
        path = []
        curr = node
        while curr:
            path.append((curr.r, curr.c))
            curr = curr.parent
        path.reverse()
        self.current_path = path
        self.path_cost = len(path) - 1
        for r, c in path:
            if (r, c) != self.start_pos and (r, c) != self.target_pos:
                self.grid[r][c].type = "path"
                self.canvas.itemconfig(self.grid[r][c].canvas_id, fill=PATH_COLOR)
        self.update_metrics()
        return path

    def _clear_visual_path(self):
        """Clear only the visual path (green cells) without touching walls."""
        for r, c in self.current_path:
            if (r, c) == self.start_pos or (r, c) == self.target_pos:
                continue
            if self.grid[r][c].type == "path":
                self.grid[r][c].type = "empty"
                self.canvas.itemconfig(self.grid[r][c].canvas_id, fill=EMPTY_COLOR)
        self.current_path = []

    # --- Animated algorithms (initial search with visualization) ---
    def run_gbfs(self, start):
        h = self.heuristic_value(start[0], start[1])
        start_node = Node(*start, h=h)
        open_list = [(h, id(start_node), start_node)]
        visited = {start}
        while open_list:
            _, _, curr = heapq.heappop(open_list)
            if (curr.r, curr.c) == self.target_pos:
                return curr
            self.animate_explored(curr.r, curr.c)
            for nr, nc in self.get_neighbors(curr.r, curr.c):
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    h = self.heuristic_value(nr, nc)
                    neighbor = Node(nr, nc, curr, h=h)
                    neighbor.f = h
                    self.animate_frontier(nr, nc)
                    heapq.heappush(open_list, (h, id(neighbor), neighbor))
        return None

    def run_astar(self, start):
        h = self.heuristic_value(start[0], start[1])
        start_node = Node(*start, g=0, h=h)
        open_list = [(start_node.f, id(start_node), start_node)]
        visited = {}
        while open_list:
            _, _, curr = heapq.heappop(open_list)
            pos = (curr.r, curr.c)
            if pos == self.target_pos:
                return curr
            if pos in visited and visited[pos] <= curr.g:
                continue
            visited[pos] = curr.g
            self.animate_explored(curr.r, curr.c)
            for nr, nc in self.get_neighbors(curr.r, curr.c):
                new_g = curr.g + 1
                if (nr, nc) not in visited or visited.get((nr, nc), float('inf')) > new_g:
                    h = self.heuristic_value(nr, nc)
                    neighbor = Node(nr, nc, curr, g=new_g, h=h)
                    self.animate_frontier(nr, nc)
                    heapq.heappush(open_list, (neighbor.f, id(neighbor), neighbor))
        return None

    def start_search(self):
        if not self.start_pos or not self.target_pos:
            messagebox.showwarning("Warning", "Place Start and Target nodes!")
            return
        self.clear_path_only()
        self.stop_flag = False
        self.set_status("Searching...", "blue")
        algo = self.algorithm.get()

        start_time = time.time()
        found_node = None
        try:
            if self.dynamic_mode.get():
                self._run_dynamic(algo)
                return
            else:
                if algo == "Greedy Best-First":
                    found_node = self.run_gbfs(self.start_pos)
                else:
                    found_node = self.run_astar(self.start_pos)

            elapsed = (time.time() - start_time) * 1000
            self.exec_time = elapsed

            if found_node:
                self.reconstruct_path(found_node)
                self.set_status("Path Found!", "green")
            else:
                self.set_status("No Path Found", "red")
            self.update_metrics()

        except StopIteration:
            pass

    def _run_dynamic(self, algo):
        """
        Dynamic Mode — fulfills all 3 requirements:
        1. Spawn obstacles with user-defined probability at every time step
        2. Detect if new obstacle blocks current path → replan immediately from agent position
        3. Efficient: only replan when obstacle is ON the current path
        """
        start_time = time.time()
        AGENT_COLOR = "#FF4500"
        prob = self.dynamic_prob.get()

        # ── helpers ──────────────────────────────────────────────
        def draw_agent(r, c):
            cs = self.cell_size
            self.canvas.delete("agent_marker")
            self.canvas.create_oval(
                c * cs + 4, r * cs + 4,
                c * cs + cs - 4, r * cs + cs - 4,
                fill=AGENT_COLOR, outline="white", width=2,
                tags="agent_marker"
            )
            self.root.update()

        def restore_cell(r, c):
            """Restore a cell the agent just left back to path colour."""
            if (r, c) != self.start_pos and (r, c) != self.target_pos:
                if self.grid[r][c].type != "wall":
                    self.grid[r][c].type = "path"
                    self.canvas.itemconfig(self.grid[r][c].canvas_id, fill=PATH_COLOR)

        def try_spawn():
            """
            Requirement 1 — attempt to spawn ONE obstacle this time step
            with probability = prob. Returns True if a wall was placed.
            """
            if random.random() >= prob:
                return False          # probability gate
            # pick any non-special, non-wall cell
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) == self.start_pos or (r, c) == self.target_pos:
                return False
            if self.grid[r][c].type == "wall":
                return False
            # place wall
            self.grid[r][c].type = "wall"
            self.canvas.itemconfig(self.grid[r][c].canvas_id, fill=WALL_COLOR)
            self.canvas.delete(f"txt_{r}_{c}")
            self.root.update()
            return True

        def replan(from_pos):
            """
            Requirement 2 & 3 — silent, fast replan from agent's current position.
            Clears only the old green path, keeps walls and explored cells.
            """
            self._clear_visual_path()
            node = self._search_silent(algo, from_pos)
            if node is None:
                return None
            return self._draw_path_silent(node)

        # ── initial animated search ──────────────────────────────
        self.clear_path_only()
        try:
            if algo == "Greedy Best-First":
                found = self.run_gbfs(self.start_pos)
            else:
                found = self.run_astar(self.start_pos)
        except StopIteration:
            return

        if not found:
            self.set_status("No Path Found", "red")
            self.exec_time = (time.time() - start_time) * 1000
            self.update_metrics()
            return

        path = self.reconstruct_path(found)
        self.root.update()
        time.sleep(0.25)

        # ── agent walk loop ──────────────────────────────────────
        idx = 0          # agent's index in path
        draw_agent(*path[0])

        while idx < len(path) - 1:
            if self.stop_flag:
                break

            # --- Requirement 1: try to spawn obstacle this time step ---
            spawned = try_spawn()

            # --- Requirement 2 & 3: check ONLY if spawn happened AND it's on path ---
            if spawned and self.path_blocked():
                self.set_status("Obstacle! Re-planning...", "#FF6600")
                agent_pos = path[idx]
                self.canvas.delete("agent_marker")
                new_path = replan(agent_pos)
                if new_path is None:
                    self.set_status("No Path Found", "red")
                    self.exec_time = (time.time() - start_time) * 1000
                    self.update_metrics()
                    return
                path = new_path
                idx = 0
                draw_agent(*path[0])
                self.root.update()
                time.sleep(0.25)
                continue

            # --- Move agent one step ---
            prev_r, prev_c = path[idx]
            idx += 1
            ar, ac = path[idx]

            self.canvas.delete("agent_marker")
            restore_cell(prev_r, prev_c)
            draw_agent(ar, ac)
            time.sleep(0.15)

        # done
        self.canvas.delete("agent_marker")
        self.exec_time = (time.time() - start_time) * 1000
        if not self.stop_flag:
            self.set_status("Target Reached!", "green")
        self.update_metrics()


# --- Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = GridApp(root)

    root.mainloop()
