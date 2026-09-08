import sys
import argparse
import time
import heapq
import collections
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Optional

# --- parser ---
@dataclass(frozen=True)
class Gate:
    id: str
    color: str
    side: str  # 't' (top), 'b' (bottom), 'l' (left), 'r' (right)
    x: int     # start x coordinate on board (0 .. w-1)
    y: int     # start y coordinate on board (0 .. h-1)
    span: int  # length along the edge

@dataclass(frozen=True)
class BlockDef:
    id: str
    color: str
    cells: Tuple[Tuple[int, int], ...]
    initial_pos: Tuple[int, int]
    direction: Optional[str] = None
    ice_count: int = 0

@dataclass
class Level:
    w: int
    h: int
    walls: Set[Tuple[int, int]]
    gates: List[Gate]
    blocks: Dict[str, BlockDef]

def parse_level(filepath: str) -> Level:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\r\n') for line in f]

    w, h = 0, 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('w='):
            w = int(line.split('=')[1])
        elif line.startswith('h='):
            h = int(line.split('=')[1])
        elif line in ('COLOR:', 'ID:', 'MODIFIERS:', 'BLOCKS:', 'EXITS:'):
            break
        i += 1

    color_grid: List[List[str]] = []
    id_grid: List[List[str]] = []
    modifiers_grid: List[List[str]] = []

    current_section = None
    section_lines: Dict[str, List[str]] = {
        'COLOR': [],
        'ID': [],
        'MODIFIERS': [],
        'BLOCKS': [],
        'EXITS': []
    }

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.endswith(':'):
            sec = line[:-1].strip()
            if sec in section_lines:
                current_section = sec
            else:
                current_section = None
        elif current_section:
            section_lines[current_section].append(line)
        i += 1

    def parse_grid_lines(raw_lines: List[str]) -> List[List[str]]:
        grid = []
        for r_line in raw_lines:
            tokens = r_line.split()
            if tokens:
                grid.append(tokens)
        return grid

    color_grid = parse_grid_lines(section_lines['COLOR'])
    id_grid = parse_grid_lines(section_lines['ID'])
    modifiers_grid = parse_grid_lines(section_lines['MODIFIERS'])

    walls: Set[Tuple[int, int]] = set()
    for r in range(1, h + 1):
        for c in range(1, w + 1):
            if r < len(color_grid) and c < len(color_grid[r]):
                cell_color = color_grid[r][c]
                if cell_color == '#':
                    walls.add((c - 1, r - 1))

    block_cells: Dict[str, List[Tuple[int, int]]] = {}
    block_colors: Dict[str, str] = {}
    block_dirs: Dict[str, Optional[str]] = {}
    block_ice: Dict[str, int] = {}

    for r in range(1, h + 1):
        for c in range(1, w + 1):
            cell_id = id_grid[r][c]
            if cell_id not in ('.', '#'):
                x, y = c - 1, r - 1
                if cell_id not in block_cells:
                    block_cells[cell_id] = []
                    block_colors[cell_id] = color_grid[r][c]
                block_cells[cell_id].append((x, y))

    for block_id, cells in block_cells.items():
        min_x = min(x for x, y in cells)
        min_y = min(y for x, y in cells)
        tag_c = min_x + 1
        tag_r = min_y + 1
        
        mod_token = '.'
        if tag_r < len(modifiers_grid) and tag_c < len(modifiers_grid[tag_r]):
            mod_token = modifiers_grid[tag_r][tag_c]
            
        b_dir = None
        b_ice = 0
        if mod_token == '-':
            b_dir = 'h'
        elif mod_token == '|':
            b_dir = 'v'
        elif mod_token.startswith('i') and mod_token[1:].isdigit():
            b_ice = int(mod_token[1:])

        block_dirs[block_id] = b_dir
        block_ice[block_id] = b_ice

    for line in section_lines.get('BLOCKS', []):
        tokens = line.split()
        if len(tokens) >= 2:
            bid = tokens[0]
            if bid not in block_cells: continue
            for token in tokens[2:]:
                if token.startswith("ic="):
                    try:
                        block_ice[bid] = int(token.split("=", 1)[1])
                    except ValueError:
                        pass
                elif token.startswith("ar="):
                    direction = token.split("=", 1)[1].lower()
                    if direction in ("h", "v"):
                        block_dirs[bid] = direction
                elif token in ("-", "|"):
                    block_dirs[bid] = "h" if token == "-" else "v"

    blocks: Dict[str, BlockDef] = {}
    for block_id, cells in block_cells.items():
        min_x = min(x for x, y in cells)
        min_y = min(y for x, y in cells)
        rel_cells = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
        blocks[block_id] = BlockDef(
            id=block_id,
            color=block_colors[block_id],
            cells=rel_cells,
            initial_pos=(min_x, min_y),
            direction=block_dirs[block_id],
            ice_count=block_ice[block_id]
        )

    gates: List[Gate] = []
    
    c = 1
    while c <= w:
        g_id = id_grid[0][c]
        if g_id not in ('.', '#'):
            g_color = color_grid[0][c]
            start_x = c - 1
            span = 0
            while c <= w and id_grid[0][c] == g_id:
                span += 1
                c += 1
            gates.append(Gate(id=g_id, color=g_color, side='t', x=start_x, y=0, span=span))
        else:
            c += 1

    c = 1
    while c <= w:
        g_id = id_grid[h + 1][c]
        if g_id not in ('.', '#'):
            g_color = color_grid[h + 1][c]
            start_x = c - 1
            span = 0
            while c <= w and id_grid[h + 1][c] == g_id:
                span += 1
                c += 1
            gates.append(Gate(id=g_id, color=g_color, side='b', x=start_x, y=h - 1, span=span))
        else:
            c += 1

    r = 1
    while r <= h:
        g_id = id_grid[r][0]
        if g_id not in ('.', '#'):
            g_color = color_grid[r][0]
            start_y = r - 1
            span = 0
            while r <= h and id_grid[r][0] == g_id:
                span += 1
                r += 1
            gates.append(Gate(id=g_id, color=g_color, side='l', x=0, y=start_y, span=span))
        else:
            r += 1

    r = 1
    while r <= h:
        g_id = id_grid[r][w + 1]
        if g_id not in ('.', '#'):
            g_color = color_grid[r][w + 1]
            start_y = r - 1
            span = 0
            while r <= h and id_grid[r][w + 1] == g_id:
                span += 1
                r += 1
            gates.append(Gate(id=g_id, color=g_color, side='r', x=w - 1, y=start_y, span=span))
        else:
            r += 1

    return Level(w=w, h=h, walls=walls, gates=gates, blocks=blocks)

# --- game ---
class GameEngine:
    def __init__(self, level: Level):
        self.level = level
        self.w = level.w
        self.h = level.h
        self.gates = level.gates
        
        self.block_defs = list(level.blocks.values())
        self.num_blocks = len(self.block_defs)
        self.idx_to_block_id = {i: b.id for i, b in enumerate(self.block_defs)}
        self.block_id_to_idx = {b.id: i for i, b in enumerate(self.block_defs)}
        
        self.ice_counts = [b.ice_count for b in self.block_defs]
        
        gate_colors = {g.color for g in self.gates}
        self.target_indices = frozenset(
            i for i, b in enumerate(self.block_defs) if b.color in gate_colors
        )
        
        self.walls_mask = 0
        for x, y in level.walls:
            self.walls_mask |= (1 << (y * self.w + x))
            
        self.valid_pos: List[List[bool]] = []
        self.block_masks: List[List[int]] = []
        self.gate_exit: List[List[bool]] = []
        
        for i, b in enumerate(self.block_defs):
            b_valid = [False] * (self.w * self.h)
            b_mask = [0] * (self.w * self.h)
            b_exit = [False] * (self.w * self.h)
            
            abs_cells_0 = b.cells
            min_dx = min(c[0] for c in abs_cells_0)
            max_dx = max(c[0] for c in abs_cells_0)
            min_dy = min(c[1] for c in abs_cells_0)
            max_dy = max(c[1] for c in abs_cells_0)

            for y in range(self.h):
                for x in range(self.w):
                    idx = y * self.w + x
                    fits = True
                    mask = 0
                    for dx, dy in b.cells:
                        cx, cy = x + dx, y + dy
                        if cx < 0 or cx >= self.w or cy < 0 or cy >= self.h:
                            fits = False
                            break
                        if (cx, cy) in level.walls:
                            fits = False
                            break
                        mask |= (1 << (cy * self.w + cx))
                    
                    if fits:
                        b_valid[idx] = True
                        b_mask[idx] = mask
                        
                        sits = False
                        for g in self.gates:
                            if g.color != b.color: continue
                            
                            if g.side == 't' and y + min_dy == 0:
                                contact = [x + cx for cx, cy in b.cells if y + cy == 0]
                                if contact and min(contact) >= g.x and max(contact) < g.x + g.span: sits = True
                            elif g.side == 'b' and y + max_dy == self.h - 1:
                                contact = [x + cx for cx, cy in b.cells if y + cy == self.h - 1]
                                if contact and min(contact) >= g.x and max(contact) < g.x + g.span: sits = True
                            elif g.side == 'l' and x + min_dx == 0:
                                contact = [y + cy for cx, cy in b.cells if x + cx == 0]
                                if contact and min(contact) >= g.y and max(contact) < g.y + g.span: sits = True
                            elif g.side == 'r' and x + max_dx == self.w - 1:
                                contact = [y + cy for cx, cy in b.cells if x + cx == self.w - 1]
                                if contact and min(contact) >= g.y and max(contact) < g.y + g.span: sits = True
                        b_exit[idx] = sits
                        
            self.valid_pos.append(b_valid)
            self.block_masks.append(b_mask)
            self.gate_exit.append(b_exit)
            
        self.slide_rays = []
        for i, b in enumerate(self.block_defs):
            b_rays = [[] for _ in range(self.w * self.h)]
            if b.direction == 'h': dirs = [(-1, 0), (1, 0)]
            elif b.direction == 'v': dirs = [(0, -1), (0, 1)]
            else: dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            
            for y in range(self.h):
                for x in range(self.w):
                    idx = y * self.w + x
                    if not self.valid_pos[i][idx]: continue
                    
                    for dx, dy in dirs:
                        ray = []
                        k = 1
                        while True:
                            nx, ny = x + k * dx, y + k * dy
                            if nx < 0 or nx >= self.w or ny < 0 or ny >= self.h: break
                            nidx = ny * self.w + nx
                            if not self.valid_pos[i][nidx]: break
                            
                            step_mask = self.block_masks[i][nidx]
                            ray.append((nidx, step_mask))
                            k += 1
                        if ray:
                            b_rays[idx].append(ray)
            self.slide_rays.append(b_rays)
            
        self.block_signatures = []
        for i, b in enumerate(self.block_defs):
            sig = (b.color, b.cells, b.direction, b.ice_count)
            self.block_signatures.append(sig)
            
        self.signature_groups = {}
        for i, sig in enumerate(self.block_signatures):
            self.signature_groups.setdefault(sig, []).append(i)
        self.sorted_signatures = sorted(self.signature_groups.keys(), key=repr)
            
        init_pos = tuple(b.initial_pos[1] * self.w + b.initial_pos[0] for b in self.block_defs)
        self.initial_state = self.apply_auto_exits(init_pos, 0, 0)

    def get_state_key(self, pos: Tuple[int, ...], exited_mask: int) -> Tuple:
        canonical = []
        for sig in self.sorted_signatures:
            active_pos = []
            exited_cnt = 0
            for i in self.signature_groups[sig]:
                if (exited_mask & (1 << i)) != 0:
                    exited_cnt += 1
                else:
                    active_pos.append(pos[i])
            canonical.append((sig, tuple(sorted(active_pos)), exited_cnt))
        return tuple(canonical)

    def is_solved(self, exited_mask: int) -> bool:
        for t_idx in self.target_indices:
            if (exited_mask & (1 << t_idx)) == 0:
                return False
        return True

    def apply_auto_exits(self, pos: Tuple[int, ...], exited_mask: int, exited_count: int) -> Tuple[Tuple[int, ...], int, int]:
        pos_list = list(pos)
        while True:
            exited_any = False
            for i in range(self.num_blocks):
                if (exited_mask & (1 << i)) != 0: continue
                if self.ice_counts[i] > exited_count: continue
                idx = pos_list[i]
                if self.gate_exit[i][idx]:
                    pos_list[i] = -1
                    exited_mask |= (1 << i)
                    exited_count += 1
                    exited_any = True
                    break
            if not exited_any:
                break
        return tuple(pos_list), exited_mask, exited_count

    def get_successors(self, pos: Tuple[int, ...], exited_mask: int, exited_count: int) -> List[Tuple[int, int, Tuple[int, ...], int, int]]:
        board_mask = 0
        for i in range(self.num_blocks):
            if (exited_mask & (1 << i)) == 0:
                board_mask |= self.block_masks[i][pos[i]]
                
        succs = []
        pos_list = list(pos)
        
        for i in range(self.num_blocks):
            if (exited_mask & (1 << i)) != 0: continue
            if self.ice_counts[i] > exited_count: continue
            
            p_idx = pos[i]
            other_mask = board_mask ^ self.block_masks[i][p_idx]
            
            for ray in self.slide_rays[i][p_idx]:
                for new_idx, step_mask in ray:
                    if (other_mask & step_mask) != 0:
                        break
                        
                    pos_list[i] = new_idx
                    if self.gate_exit[i][new_idx]:
                        next_pos, next_mask, next_cnt = self.apply_auto_exits(tuple(pos_list), exited_mask, exited_count)
                    else:
                        next_pos, next_mask, next_cnt = tuple(pos_list), exited_mask, exited_count
                        
                    succs.append((i, new_idx, next_pos, next_mask, next_cnt))
                    
            pos_list[i] = p_idx
            
        return succs

# --- heuristics ---
class HeuristicCalculator:
    def __init__(self, engine: GameEngine, ice_multiplier: int = 3):
        self.engine = engine
        self.w = engine.w
        self.h = engine.h
        self.num_blocks = engine.num_blocks
        self.target_indices = engine.target_indices
        self.ice_counts = engine.ice_counts
        self.ice_multiplier = ice_multiplier

        self.min_moves = []
        for i in range(self.num_blocks):
            m_arr = [9999] * (self.w * self.h)
            if i not in self.target_indices:
                self.min_moves.append(m_arr)
                continue
                
            q = collections.deque()
            for idx in range(self.w * self.h):
                if engine.gate_exit[i][idx]:
                    m_arr[idx] = 0
                    q.append(idx)
            
            reverse_edges = [[] for _ in range(self.w * self.h)]
            for idx in range(self.w * self.h):
                for ray in engine.slide_rays[i][idx]:
                    for nidx, mask in ray:
                        reverse_edges[nidx].append(idx)
                    
            while q:
                curr = q.popleft()
                c_dist = m_arr[curr]
                for prev in reverse_edges[curr]:
                    if m_arr[prev] > c_dist + 1:
                        m_arr[prev] = c_dist + 1
                        q.append(prev)
                        
            self.min_moves.append(m_arr)

    def compute_h(self, pos: tuple, exited_mask: int, exited_count: int) -> int:
        h_sum = 0
        for t_idx in self.target_indices:
            if (exited_mask & (1 << t_idx)) != 0:
                continue
            d = self.min_moves[t_idx][pos[t_idx]]
            if d >= 9000:
                return 999999
            h_sum += d

        ice_penalty = 0
        for i in range(self.num_blocks):
            if (exited_mask & (1 << i)) == 0:
                needed = self.ice_counts[i] - exited_count
                if needed > 0:
                    ice_penalty += needed

        return h_sum + (self.ice_multiplier * ice_penalty)

# --- complete_solver ---
class CompleteAStarSolver:
    def __init__(self, level: Level, time_limit: float = 60.0, verbose: bool = False):
        self.level = level
        self.time_limit = time_limit
        self.verbose = verbose
        self.engine = GameEngine(level)
        self.heuristic = HeuristicCalculator(self.engine, ice_multiplier=0)

    def solve(self) -> Tuple[str, List[Tuple[str, int, int]], int, int, int, float]:
        start_time = time.time()
        s0 = self.engine.initial_state

        if self.engine.is_solved(s0[1]):
            return "SOLVED", [], 0, 0, 0, time.time() - start_time

        status, path, exp, gen, uniq, t = self._run_astar(s0, 1.0, start_time, 10_000_000)
        if status == "SOLVED" or status == "UNSOLVABLE":
            return status, path, exp, gen, uniq, time.time() - start_time

        return "TIMEOUT", [], 0, 0, 0, time.time() - start_time

    def _run_astar(self, s0: Tuple[Tuple[int, ...], int, int], weight: float, global_start_time: float, node_budget: int):
        open_set = []
        pos0, mask0, cnt0 = s0
        h0 = self.heuristic.compute_h(pos0, mask0, cnt0)
        counter = 0
        heapq.heappush(open_set, (weight * h0, h0, counter, 0, pos0, mask0, cnt0, None))

        key0 = self.engine.get_state_key(pos0, mask0)
        best_g: Dict[Tuple, int] = {key0: 0}
        expanded_nodes = 0
        generated_nodes = 0

        while open_set:
            if time.time() - global_start_time >= self.time_limit:
                return "TIMEOUT", [], expanded_nodes, generated_nodes, len(best_g), time.time() - global_start_time

            if expanded_nodes >= node_budget:
                return "TIMEOUT", [], expanded_nodes, generated_nodes, len(best_g), time.time() - global_start_time

            f, _h_tie, _, g, pos, mask, cnt, path_node = heapq.heappop(open_set)
            current_key = self.engine.get_state_key(pos, mask)
            
            if g != best_g.get(current_key):
                continue

            if self.engine.is_solved(mask):
                path = []
                curr = path_node
                while curr is not None:
                    move, curr = curr
                    path.append(move)
                path.reverse()
                return "SOLVED", path, expanded_nodes, generated_nodes, len(best_g), time.time() - global_start_time

            expanded_nodes += 1

            for b_idx, nidx, npos, nmask, ncnt in self.engine.get_successors(pos, mask, cnt):
                generated_nodes += 1
                next_g = g + 1
                next_key = self.engine.get_state_key(npos, nmask)
                
                if next_g >= best_g.get(next_key, float('inf')):
                    continue

                h_val = self.heuristic.compute_h(npos, nmask, ncnt)
                if h_val >= 999999:
                    continue
                    
                best_g[next_key] = next_g
                f_val = next_g + weight * h_val
                counter += 1
                
                b_id = self.engine.idx_to_block_id[b_idx]
                move = (b_id, nidx % self.engine.w, nidx // self.engine.w)
                
                heapq.heappush(open_set, (f_val, h_val, counter, next_g, npos, nmask, ncnt, (move, path_node)))

        return "UNSOLVABLE", [], expanded_nodes, generated_nodes, len(best_g), time.time() - global_start_time

# --- fast_solver ---
class FastSolver:
    def __init__(self, level: Level, time_limit: float = 60.0, verbose: bool = False):
        self.level = level
        self.time_limit = time_limit
        self.verbose = verbose
        self.engine = GameEngine(level)
        self.heuristic = HeuristicCalculator(self.engine)

    def solve(self) -> Tuple[str, List[Tuple[str, int, int]], int, int, int, float]:
        start_time = time.time()
        s0 = self.engine.initial_state

        if self.engine.is_solved(s0[1]):
            return "SOLVED", [], 0, 0, 0, time.time() - start_time

        open_set = []
        pos0, mask0, cnt0 = s0
        h0 = self.heuristic.compute_h(pos0, mask0, cnt0)
        counter = 0
        
        heapq.heappush(open_set, (h0, counter, pos0, mask0, cnt0, None))

        key0 = self.engine.get_state_key(pos0, mask0)
        visited = {key0}
        expanded_nodes = 0
        generated_nodes = 0
        
        budget = 500000

        while open_set:
            if time.time() - start_time >= self.time_limit:
                return "TIMEOUT", [], expanded_nodes, generated_nodes, len(visited), time.time() - start_time

            if expanded_nodes >= budget:
                return "TIMEOUT", [], expanded_nodes, generated_nodes, len(visited), time.time() - start_time

            h, _, pos, mask, cnt, path_node = heapq.heappop(open_set)

            if self.engine.is_solved(mask):
                path = []
                curr = path_node
                while curr is not None:
                    move, curr = curr
                    path.append(move)
                path.reverse()
                return "SOLVED", path, expanded_nodes, generated_nodes, len(visited), time.time() - start_time

            expanded_nodes += 1

            for b_idx, nidx, npos, nmask, ncnt in self.engine.get_successors(pos, mask, cnt):
                generated_nodes += 1
                next_key = self.engine.get_state_key(npos, nmask)
                
                if next_key in visited:
                    continue
                visited.add(next_key)

                h_val = self.heuristic.compute_h(npos, nmask, ncnt)
                if h_val >= 999999:
                    continue
                    
                counter += 1
                b_id = self.engine.idx_to_block_id[b_idx]
                move = (b_id, nidx % self.engine.w, nidx // self.engine.w)
                
                heapq.heappush(open_set, (h_val, counter, npos, nmask, ncnt, (move, path_node)))

        return "UNSOLVABLE", [], expanded_nodes, generated_nodes, len(visited), time.time() - start_time

# --- fringe_solver ---
class FringeSolver:
    def __init__(self, level: Level, time_limit: float = 60.0, verbose: bool = False):
        self.level = level
        self.time_limit = time_limit
        self.verbose = verbose
        self.engine = GameEngine(level)
        self.heuristic = HeuristicCalculator(self.engine)

    def solve(self) -> Tuple[str, List[Tuple[str, int, int]], int, int, int, float]:
        start_time = time.time()
        s0 = self.engine.initial_state

        if self.engine.is_solved(s0[1]):
            return "SOLVED", [], 0, 0, 0, time.time() - start_time

        pos0, mask0, cnt0 = s0
        h0 = self.heuristic.compute_h(pos0, mask0, cnt0)
        
        if h0 >= 999999:
            return "UNSOLVABLE", [], 0, 0, 0, time.time() - start_time

        f_limit = h0
        now = [(0, pos0, mask0, cnt0, None)]
        later = []
        
        key0 = self.engine.get_state_key(pos0, mask0)
        best_g: Dict[Tuple, int] = {key0: 0}
        
        expanded_nodes = 0
        generated_nodes = 0
        
        while now:
            if time.time() - start_time >= self.time_limit:
                return "TIMEOUT", [], expanded_nodes, generated_nodes, len(best_g), time.time() - start_time

            f_min = float('inf')
            
            while now:
                if time.time() - start_time >= self.time_limit:
                    return "TIMEOUT", [], expanded_nodes, generated_nodes, len(best_g), time.time() - start_time

                g, pos, mask, cnt, path_node = now.pop()
                current_key = self.engine.get_state_key(pos, mask)
                
                if g > best_g.get(current_key, float('inf')):
                    continue
                    
                if self.engine.is_solved(mask):
                    path = []
                    curr = path_node
                    while curr is not None:
                        move, curr = curr
                        path.append(move)
                    path.reverse()
                    return "SOLVED", path, expanded_nodes, generated_nodes, len(best_g), time.time() - start_time
                    
                h_val = self.heuristic.compute_h(pos, mask, cnt)
                f = g + h_val
                
                if f > f_limit:
                    f_min = min(f, f_min)
                    later.append((g, pos, mask, cnt, path_node))
                    continue
                    
                expanded_nodes += 1
                
                for b_idx, nidx, npos, nmask, ncnt in self.engine.get_successors(pos, mask, cnt):
                    generated_nodes += 1
                    next_g = g + 1
                    next_key = self.engine.get_state_key(npos, nmask)
                    
                    if next_g >= best_g.get(next_key, float('inf')):
                        continue
                        
                    child_h = self.heuristic.compute_h(npos, nmask, ncnt)
                    if child_h >= 999999:
                        continue
                        
                    best_g[next_key] = next_g
                    
                    b_id = self.engine.idx_to_block_id[b_idx]
                    move = (b_id, nidx % self.engine.w, nidx // self.engine.w)
                    
                    now.append((next_g, npos, nmask, ncnt, (move, path_node)))
            
            if f_min == float('inf'):
                break
                
            f_limit = f_min
            later.reverse()
            now = later
            later = []

        return "UNSOLVABLE", [], expanded_nodes, generated_nodes, len(best_g), time.time() - start_time

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description="Color Block Crush Solver CLI")
    parser.add_argument("level", help="Path to level ASCII file")
    parser.add_argument("--solver", choices=["complete", "fast", "fringe"], default="complete", help="Solver type")
    parser.add_argument("--verbose", action="store_true", help="Print debug info to stderr")

    args = parser.parse_args()

    try:
        level = parse_level(args.level)
    except Exception as e:
        sys.stderr.write(f"Error parsing level file: {e}\n")
        sys.exit(1)

    start_time = time.time()

    if args.solver == "fast":
        solver = FastSolver(level, time_limit=60.0, verbose=args.verbose)
    elif args.solver == "fringe":
        solver = FringeSolver(level, time_limit=60.0, verbose=args.verbose)
    else:
        solver = CompleteAStarSolver(level, time_limit=60.0, verbose=args.verbose)

    status, moves, expanded_nodes, generated_nodes, unique_states, elapsed_time = solver.solve()

    if args.verbose:
        sys.stderr.write(f"[DEBUG] Status: {status}\n")
        sys.stderr.write(f"[DEBUG] Expanded Nodes: {expanded_nodes}\n")
        sys.stderr.write(f"[DEBUG] Elapsed Time: {elapsed_time:.4f}s\n")
        sys.stderr.write(f"[DEBUG] Moves Count: {len(moves)}\n")

    # Output strictly according to assignment format on stdout
    print(f"STATUS: {status}")
    if status == "SOLVED":
        print(f"MOVES: {len(moves)}")
        for b_id, x, y in moves:
            print(f"{b_id} {x} {y}")

if __name__ == "__main__":
    main()
