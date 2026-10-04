# Quantum Nexus Core — Technical Specification

**Designation:** QNC-1 (reference implementation)
**Architect:** Ahkeem — named 2026-10-03
**Status:** Working prototype. All values below are exact to the reference implementation (`quantum_nexus_core.py`).
**License:** MIT

---

## 1. System overview

The Quantum Nexus Core is a self-modifying AI architecture built from five subsystems:

| # | Subsystem | Role |
|---|---|---|
| 1 | ErrorLoop core | Recurrent predictive-coding loop; the thinking engine. Never settles. |
| 2 | Qubit belief module | Holds propositions as yes/no superpositions; measurement = decision. |
| 3 | Real-time decoder | Reads hidden state into output numbers every timestep. |
| 4 | Snapshot system | Deep-freezes the loop at generation boundaries; immutable lineage. |
| 5 | Evolution engine | Mutated copies compete; lowest error seeds the next generation. |

Three timescales: **timesteps** (thinking), **measurements** (deciding), **generations** (improving).

---

## 2. ErrorLoop core (Loop A)

### 2.1 State

| Symbol | Shape | Init | Description |
|---|---|---|---|
| `h` | (d,) | zeros | Hidden state — "what the loop is thinking" |
| `W` | (d, d) | N(0, 0.5) | Recurrent weights — self-mutating |
| `U` | (d,) | N(0, 0.5) | Input weights |
| `V` | (d,) | N(0, 0.5) | Prediction readout — **this is the decoder** |

Reference hyperparameter: **d = 6** (hidden dimension).

### 2.2 Update equations (per timestep)

```
y_pred = V · h                          (decode: state -> number, real time)
err    = y_true - y_pred                 (the error signal: the loop's fuel)
h      = tanh(W·h + U·x + 0.3·err·V)     (state chases the error away)
W     += lr · outer(err·V, h)            (weights rewrite themselves...)
V     += lr · err·h                      (...every single step)
```

Reference hyperparameter: **lr = 0.05** (learning rate).

### 2.3 Dynamics guarantee

The loop has no fixed point by design: `W` and `V` are rewritten every
timestep, so the system perpetually shifts its way of thinking. Observed
reference behavior: mean |ΔW| drifts 0.001 → 0.090 over 40 timesteps —
the structure is always moving, never converged.

### 2.4 World model (reference)

The loop tracks a drifting target stream (the "world"):

```
y_true(t) = sin(0.3·t) + 0.5·sin(0.11·t + 1.0)
x(t)      = 0.5·sin(0.05·t)
```

`t_steps = 40` per episode. The world never stands still, so neither does the loop.

---

## 3. Qubit belief module

### 3.1 Representation

Each proposition is held as a two-state superposition:

```
|ψ> = cos(φ/2)|yes> + sin(φ/2)|no>
p(yes) = cos²(φ/2)
```

Init: **φ = π/2** (maximally undecided: 50/50).

### 3.2 Update rule (evidence rotation)

Per timestep, the decoder's output is compared against the world:

```
agree = sign(y_pred) == sign(y_true)     (did the decoder match the world?)
φ    -= 0.22 · (+1 if agree else -1)     (evidence rotates the amplitude)
φ     = clip(φ, 0.05, π - 0.05)          (never fully collapses until measured)
```

### 3.3 Measurement = decision

Acting on a belief is measurement: the superposition collapses to YES with
probability p(yes). Reference behavior (seed 16): p(yes) travels
0.39 → 0.81 → 1.00 → … → **0.999**, i.e. the system holds yes *and* no,
then decides YES with 99.9% confidence.

### 3.4 Reference proposition

`"my decoded sign matches the world"` — |0⟩ = yes, |1⟩ = no. The module is
proposition-agnostic: any yes/no question can be mounted on it.

---

## 4. Real-time decoder

The decoder is the `V` readout matrix: **hidden state → output number,
every timestep, no batching.**

```
y_pred = V · h
```

It is linear in the reference implementation (the simplest possible
decoder). It is also the evolvable part: the evolution engine mutates `V`,
so the lineage's "way of reading its own thoughts" is what improves.

---

## 5. Snapshot system

### 5.1 Semantics

At each generation boundary, the live loop is deep-copied:

```
snapshot = deepcopy(live_loop)
```

The snapshot is **immutable**: the live loop continues mutating, but the
frozen copy cannot be touched. Verified in the reference run: live loop's
mean |ΔW| drifts 0.001 → 0.090 while `snapshot.W` is bit-identical before
and after (`snapshot untouched: True`, hard assert).

### 5.2 Why it exists

This is the answer to the self-modification corruption problem. The infinite
loop's chaos is quarantined: mutation happens only to *copies* of frozen
snapshots, never to the lineage itself. The parent is always recoverable.

---

## 6. Evolution engine (Loop B)

### 6.1 Procedure (per generation)

```
parent   = champion.snapshot()          # freeze at the boundary
for v in 0..3:                          # 4 variants
    cand      = deepcopy(parent)        # every variant starts frozen-identical
    cand.h    = zeros(d)                # fresh episode; WEIGHTS are the heredity
    if v > 0:
        cand.V += N(0, 0.02)            # mutate the decoder (variant 0 = exact copy)
    run 40 timesteps, record mean|err|
champion = argmin(mean|err|)            # selection: lowest error wins
```

### 6.2 Invariants

- **Elitism:** variant 0 is always an exact copy — the lineage never regresses.
- **Heredity is the weights:** hidden state resets each episode; what is
  inherited is `W`, `U`, `V`.
- **Selection signal:** mean absolute prediction error over the episode.
  ("Better" = lower prediction error — the narrow, honest fitness function.)

### 6.3 Reference hyperparameters

| Parameter | Value |
|---|---|
| Generations | 8 |
| Variants per generation | 4 |
| Decoder mutation σ | 0.02 |
| Timesteps per episode | 40 |
| Random seed | 16 (reproduces the reference numbers exactly) |

### 6.4 Reference results (seed 16)

```
gen 0  0.4441
gen 1  0.3522
gen 2  0.2994
gen 3  0.2717
gen 4  0.2416
gen 5  0.2153
gen 6  0.1979
gen 7  0.1822
```

Error falls **every generation**, 0.4441 → 0.1822 (**59.0% lower**, monotonic).

---

## 7. Interfaces

### 7.1 CLI (reference implementation)

```
python3 quantum_nexus_core.py [--generations N] [--seed S] [--quiet]
```

Requires: numpy only. Runtime: ~1 second.

### 7.2 Return contract

`run()` returns a dict:

| Key | Type | Reference value |
|---|---|---|
| `belief_final` | float | 0.999 |
| `snapshot_untouched` | bool | True |
| `err_start` | float | 0.4441 |
| `err_end` | float | 0.1822 |
| `err_curve` | list[float] | 8 values, monotonic decreasing |

### 7.3 Neural Lab integration

| Surface | Form |
|---|---|
| Preset 16 | "Quantum Nexus Core" — full pipeline under Chaquopy |
| Console | `evoloop [generations]` — JS twin of the pipeline |
| 🌀 Nexus visualizer | Live watch: thinking heatmap, belief dial, snapshot freeze-frame, evolution curve |
| Run recorder (v33) | "Save this run?" prompt → timestamped JSON + TXT in `nexus-runs/` |

---

## 8. Verification spec

The reference implementation self-verifies with hard asserts:

1. **Snapshot immutability:** `assert snapshot.W == frozen_W` after live mutation.
2. **Belief convergence:** `assert p(yes)_final > 0.8`.
3. **Evolution improvement:** `assert err_end < err_start`.

Reproduction: `python3 quantum_nexus_core.py` (seed 16 default) must print
`0.4441 -> 0.1822 (59.0% lower)` and `final p(yes) = 0.999`.

---

## 9. File manifest (reference repo)

| File | Purpose |
|---|---|
| `quantum_nexus_core.py` | Reference implementation (~200 lines, numpy-only) |
| `SPECS.md` | This document |
| `README.md` | Narrative writeup with architecture diagram |
| `lesswrong-draft.md` | Forum post draft |
| `LICENSE` | MIT |

---

## 10. Version history

| Version | Date | Change |
|---|---|---|
| QNC-1 | 2026-10-03 | Theorized out loud and built the same day. First phone run 17:14 EDT. Named by Ahkeem that evening. |

---

## 11. Open problems (future work)

1. **The fitness function.** "Better" currently = lower prediction error on a
   drifting sine mixture. Scaling the *criterion* of improvement is the same
   open problem every self-improving system faces.
2. **Deeper decoders.** The linear `V` readout is the simplest decoder; a
   nonlinear readout changes what evolution can discover.
3. **Multi-proposition beliefs.** One qubit per proposition; entangled
   propositions (correlated beliefs) are unimplemented.
4. **The halting signal.** The loop currently runs a fixed 40 steps; a
   learned "done thinking" signal is future work.
5. **Quantum hardware target.** The "quantum language" is state-vector math
   on a classical CPU. Compiling the core to real quantum circuits is
   uncharted.

---

*Designed by Ahkeem, 2026-10-03 — theorized out loud, built the same day,
first ran on his phone at 17:14 EDT.*
