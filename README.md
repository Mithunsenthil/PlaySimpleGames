# Color Block Crush Solver

A high-performance Python solver for the **Color Block Crush** puzzle, implementing search algorithms, state representation, collision detection, and auto-exit mechanics.

---

## Requirements & Setup

- **Python Version**: Python 3.8+
- **Dependencies**: Uses standard Python library modules (`heapq`, `collections`, `dataclasses`, `typing`, `argparse`, `time`, `sys`). Zero external pip dependencies required.

```bash
pip install -r requirements.txt
```

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
- **MOVES**: Total number of moves $N$
- Each following line represents a slide: `<block_id> <x> <y>` where $(x, y)$ is the new top-left position of the block.

---

## Project Structure

- `solve.py` — The standalone solver containing all search logic and game mechanics.
- `requirements.txt` — Empty file (only standard libraries used) as per submission requirements.
- `test_levels/` — Directory containing the ASCII puzzle text files.
