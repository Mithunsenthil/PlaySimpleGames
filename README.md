# Color Block Crush Solver

A high-performance Python solver for the **Color Block Crush** puzzle, implementing search algorithms, state representation, collision detection, and auto-exit mechanics.

---

## Requirements & Setup

- **Python Version**: Python 3.8+
- **Dependencies**: Uses standard Python library modules (`heapq`, `collections`, `dataclasses`, `typing`, `argparse`, `time`, `sys`). **Zero external pip dependencies required.**

No installation is needed. You can run the solver directly.

---

## How to Run

Use the command-line interface (`solve.py`) to solve level files in ASCII format.

### Basic Usage

```bash
# Solve a level (defaults to complete solver)
python solve.py test_levels/test1.txt

# Specify solver type (complete, fast, or fringe)
python solve.py test_levels/test1.txt --solver complete
python solve.py test_levels/test1.txt --solver fast
python solve.py test_levels/test1.txt --solver fringe

# Enable debug logging to stderr
python solve.py test_levels/test1.txt --solver complete --verbose
```

---

## Output Format

`solve.py` outputs strictly formatted text to `stdout`:

```text
STATUS: SOLVED
MOVES: 2
1 2 0
0 0 3
```

- **STATUS**: `SOLVED`, `UNSOLVABLE`, or `TIMEOUT`
- **MOVES**: Total number of moves N
- Each following line represents a slide: `<block_id> <x> <y>` where (x, y) is the new top-left position of the block.

### Verbose Output

If you run the solver with the `--verbose` flag, it will print performance metrics and search statistics to `stderr` before printing the standard output:

```text
[DEBUG] Status: SOLVED
[DEBUG] Expanded Nodes: 2
[DEBUG] Elapsed Time: 0.0008s
[DEBUG] Moves Count: 2
STATUS: SOLVED
MOVES: 2
1 2 0
0 0 3
```

---

## Project Structure

- `solve.py` — The standalone solver containing all search logic and game mechanics.
- `Write-up.md` / `Write-up.pdf` — Detailed documentation explaining the architecture, algorithms, and performance optimizations.
- `test_levels/` — Directory containing the ASCII puzzle text files.
