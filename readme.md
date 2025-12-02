# Evolution Simulator

Minimalistic visualization of evolution and artificial life simulation.  
The Python backend calculates the world (cells, substances, physics), while the frontend, written in pure HTML/JS via WebSocket, displays everything as a “living” field.

---

## What is this project?

The goal of the project is not a “game with rules,” but **emergent evolution**:

- The world is a discrete grid (`width × height`), with **substances** stored in each cell.
- **Cells** live in the world, each with:
  - a position in continuous coordinates (`x, y`);
  - energy, health, age;
  - a set of **genes** (receptor → trigger → action).
- Substances can be:
  - `ORGANIC` — organic matter/food;
  - `INORGANIC` — inorganic matter (background, resources, signals, etc.);
  - `TOXIN` — toxins/poison.
- Cells move, absorb substances, release toxins, divide, and mutate.
Complex behavior arises from simple local rules.

---

## Demo

![Evolution Simulator Demo](preview_01.png)

## How to run the project

### 1. Clone the repository
```bash
git clone https://github.com/your-user/evolution-simulator.git
cd evolution-simulator
```

### 2. Install dependencies (Requires Python 3.10+)
```bash
pip install -r requirements.txt
```

### 3. Run project
As server with GUI
```bash
python server.py
```
or as script
```bash
python main.py
```
