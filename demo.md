# CS5205: Advanced Artificial Intelligence Lab — Assignment 5  
## SAT-based Short-term Course Scheduling

**Date:** 20/02/2026

---

## 1. Problem Statement

We are given:
- **M** rooms
- **N** short-term courses

For each course \(i\):
- **Duration** \(t_i\) (number of consecutive days)
- **Preferred start day** \(s_i\) and **deadline** \(d_i\) (must finish by \(d_i\))

**Constraints:**
- Each course runs on **consecutive days** (no day-break).
- Each course uses **exactly one room** for all its days.
- No two courses can use the same room on overlapping days.

**Decision problem:** Does there exist a schedule such that every course runs for \(t_i\) consecutive days within \([s_i, d_i]\) in a single room without conflicts?

---

## 2. SAT Formulation

### 2.1 Option-1: Encoding with \(z_{ijt}\)

**Variable:**  
\(z_{ijt}\) = 1 iff course \(i\) **starts** on day \(t\) in room \(j\).

**Indices:**
- \(i \in \{0,\ldots,N-1\}\) (course)
- \(j \in \{1,\ldots,M\}\) (room)
- \(t \in [s_i, d_i - t_i + 1]\) (valid start day so that course finishes by \(d_i\))

**Number of variables:**  
\(\sum_{i=0}^{N-1} M \cdot |\{\,t : s_i \le t \le d_i - t_i + 1\,\}|\).

**Constraints:**

1. **Each course starts exactly once**  
   For each course \(i\): exactly one of the variables \(z_{ijt}\) (over all \(j,t\)) is true.  
   - **At least one:** one clause \(\bigvee_{j,t} z_{ijt}\).  
   - **At most one:** for every pair \((j,t) \neq (j',t')\): \(\neg z_{ijt} \vee \neg z_{ij't'}\).

2. **No overlap in the same room**  
   For each room \(j\), for every pair of courses \((i, i')\) and every pair of start days \((t, t')\) such that the intervals \([t, t+t_i-1]\) and \([t', t'+t_{i'}-1]\) overlap:  
   \(\neg z_{ijt} \vee \neg z_{i'jt'}\).

**Clause structure:**
- One long “at-least-one” clause per course.
- Many binary clauses for “at-most-one” (pairwise).
- Many binary clauses for no-overlap.

So we get **many variables** (one per \((i,j,t)\)) and **mostly binary clauses**.

---

### 2.2 Option-2: Encoding with \(x_{ij}\) and \(y_{it}\)

**Variables:**
- \(x_{ij}\) = 1 iff course \(i\) is **assigned to room** \(j\).
- \(y_{it}\) = 1 iff course \(i\) **starts on day** \(t\) (with \(t \in [s_i, d_i - t_i + 1]\)).

**Number of variables:**  
\(N \cdot M + \sum_{i=0}^{N-1} |\{\,t : s_i \le t \le d_i - t_i + 1\,\}|\).

**Constraints:**

1. **Each course in exactly one room**  
   For each \(i\): exactly one \(x_{ij}\) is true.  
   - At least one: \(\bigvee_j x_{ij}\).  
   - At most one: \(\neg x_{ij} \vee \neg x_{ij'}\) for \(j \neq j'\).

2. **Each course starts exactly once**  
   For each \(i\): exactly one \(y_{it}\) is true (over valid \(t\)).  
   - At least one: \(\bigvee_t y_{it}\).  
   - At most one: \(\neg y_{it} \vee \neg y_{it'}\) for \(t \neq t'\).

3. **No overlap in the same room**  
   For each room \(j\), for every pair of courses \((i, i')\) and every pair of start days \((t, t')\) such that the runs of \(i\) from \(t\) and \(i'\) from \(t'\) overlap:  
   \(\neg x_{ij} \vee \neg x_{i'j} \vee \neg y_{it} \vee \neg y_{i't'}\).

So we get **fewer variables** than Option-1 (no \(j\) in the start variable), but **4-literal clauses** for conflicts instead of binary.

---

## 3. Comparison of Encodings

| Criterion | Option-1 (\(z_{ijt}\)) | Option-2 (\(x_{ij}, y_{it}\)) |
|-----------|------------------------|--------------------------------|
| **Variables** | \(O(N \cdot M \cdot T)\) where \(T\) = max valid start range | \(O(N \cdot M + N \cdot T)\) — fewer |
| **Clause length** | Mostly 2 literals (binary) | Mix of 2 and **4** literals |
| **Clause count** | Many “at-most-one” pairs + overlap binaries | Fewer “at-most-one” pairs, but many 4-literal conflict clauses |
| **Solver behaviour** | Modern CDCL solvers often do well on binary CNF | 4-literal clauses can sometimes slow propagation |

**Typical observation:**  
- **Option-1** has more variables and more clauses, but all clauses are short (mainly binary).  
- **Option-2** has fewer variables and often fewer total clauses, but the conflict clauses are 4-ary.  

Performance (time/memory) depends on the instance and the solver; the benchmark section below gives concrete numbers.

---

## 4. DIMACS CNF Format

Both encodings are written in **DIMACS CNF**:
- Comment lines: `c ...`
- Header: `p cnf <num_vars> <num_clauses>`
- Each clause: space-separated literals (positive = variable, negative = negated), ending with `0`.

The script writes:
- `out_enc1.cnf` for Option-1,
- `out_enc2.cnf` for Option-2  
(or a user-defined prefix with `--dimacs`).

---

## 5. Solvers Used

1. **Z3** — SMT/SAT solver; used by loading the DIMACS and solving with the Z3 Python API.  
2. **MiniSat** — Classic CDCL SAT solver (SAT Competition).  
3. **Glucose** — CDCL solver with conflict-driven clause learning (SAT Competition).  
4. **CryptoMiniSat** — Another SAT Competition solver.

Z3 is run via the script; MiniSat, Glucose, and CryptoMiniSat are run as **external executables** (must be in PATH).

---

## 6. Random Test-case Generator

The generator produces instances with:
- \(M\) rooms and \(N\) courses (configurable ranges),
- For each course: random duration, start day, and deadline such that the course can legally finish by the deadline.

**Usage:**
- Generate 100 instances:  
  `python assg05.py --generate 100 --gen-dir generated_instances`
- Run benchmark on them:  
  `python assg05.py --benchmark --bench-dir generated_instances`

Output: CSV with variables, clauses, clause size counts (binary, ternary, 4+), and per-solver result (SAT/UNSAT/TIMEOUT) and runtime.

---

## 7. Comparative Study (What to Report)

From the benchmark CSV you can compare:

- **Variables and clauses:** Option-1 vs Option-2 for the same instance.
- **Clause length distribution:** 2-, 3-, and 3+ literal counts for each encoding.
- **Computation time:** Per solver and per encoding (and aggregate over 100 instances).
- **Memory:** If available from solver output (e.g. peak memory), include; otherwise note “not measured”.
- **Consistency:** All solvers should agree on SAT/UNSAT for each instance; any discrepancy should be reported.

**Conclusion:** Summarise which encoding is “better” under which metric (e.g. “Option-1 is faster with Solver X on average”, “Option-2 uses fewer variables”), and which solver performed best on your test set.

---

## 8. How to Run

```bash
# Install Z3 (optional, for built-in Z3 solving)
pip install z3-solver

# Generate 100 random instances
python assg05.py --generate 100

# Run benchmark (generates DIMACS, runs all solvers, writes CSV)
python assg05.py --benchmark

# Single instance: sample input (no file = use built-in sample)
python assg05.py

# Single instance from file, both encodings, all solvers
python assg05.py sample_input.txt --encoding both --solver all --dimacs out

# Only Option-1, only Z3
python assg05.py sample_input.txt --encoding 1 --solver z3 --dimacs out
```

**Note:** For MiniSat/Glucose/CryptoMiniSat, install the solvers and add them to your PATH. Under Windows, use `minisat.exe`, `glucose.exe`, or `cryptominisat5.exe` as appropriate.

---

## 9. References

- DIMACS CNF format (SAT Competition).
- Z3: https://github.com/Z3Prover/z3  
- MiniSat: http://minisat.se/  
- Glucose: http://www.labri.fr/perso/lsimon/glucose/  
- CryptoMiniSat: https://www.msoos.org/cryptominisat5/
