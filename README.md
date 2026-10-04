# Quantum Nexus Core

**Ahkeem's self-modifying AI architecture. Named by Ahkeem, 2026.**

The core thinking part of an AI shouldn't be a fixed program. It should be an
infinite mathematical loop driven by its own error -- constantly shifting how
it thinks -- with a real-time decoder reading its state, and a second loop
that copies, freezes, and improves it generation after generation. Beliefs are
held the way a qubit holds them: yes *and* no at once, until the moment of
decision.

```bash
python3 quantum_nexus_core.py   # numpy only. ~1 second. Watch it think.
```

---

## What it is

Five pieces, one loop:

1. **ErrorLoop core** -- a recurrent predictive-coding loop. It predicts the
   world, measures its own error, and rewrites its own weights *every
   timestep*. It never settles. The error signal is the loop's fuel: the main
   code is constantly shifting its way of thinking.
2. **Qubit beliefs** -- a proposition ("my decoded sign matches the world")
   is held as a|yes> + b|no>. Evidence rotates the amplitudes. Acting on a
   belief is measurement: the superposition collapses to a decision.
3. **Real-time decoder** -- the prediction readout (the V matrix). Hidden
   state -> output number, every timestep, no batching.
4. **Immutable snapshots** -- at each generation boundary the live loop is
   deep-frozen into a copy. The live loop keeps mutating; the snapshot
   cannot be touched. This is what makes self-modification safe: the chaos
   of the infinite loop is quarantined away from the lineage.
5. **Evolution** -- mutated copies of the frozen snapshot compete. Lowest
   prediction error wins and seeds the next generation. Variant 0 is always
   an exact copy (elitism: the lineage never regresses).

## Architecture

```
                        +-----------------------------+
                        |          THE WORLD          |
                        |   (drifting signal stream)  |
                        +--------------+--------------+
                                       | y_true
                                       v
 +------------------------------------------------------------------+
 |                     ERRORLOOP CORE (Loop A)                      |
 |                                                                  |
 |   hidden state h --> [V decoder] --> y_pred --> error = y - y_pred|
 |        ^                                                        |
 |        |  h = tanh(W.h + U.x + 0.3*err*V)   <-- state chases     |
 |        |                                     the error away     |
 |        +--- W += lr * outer(err*V, h)  <-- weights rewrite      |
 |              V += lr * err * h            themselves EVERY STEP  |
 |                                                                  |
 |   never settles. mean |dW| keeps drifting: 0.001 -> 0.090        |
 +----------------------------------+-------------------------------+
                                    |
                    generation boundary: SNAPSHOT (deep-freeze)
                                    |
                                    v
 +------------------------------------------------------------------+
 |              GENERATION LOOP (Loop B: the copies)                |
 |                                                                  |
 |   frozen snapshot ---> variant 0: exact copy (elitism)           |
 |                   +-> variant 1..3: decoder V mutated            |
 |                                                                  |
 |   each variant runs a fresh episode; weights are the heredity    |
 |   lowest mean|err| wins --> becomes the parent of generation n+1 |
 |                                                                  |
 |   gen 0  0.4441                                                  |
 |   gen 1  0.3522                                                  |
 |   gen 2  0.2994   ...error falls every generation...             |
 |   gen 7  0.1822   (59% lower, monotonic)                         |
 +------------------------------------------------------------------+

              QUBIT BELIEF (runs alongside, per proposition)
 +------------------------------------------------------------------+
 |  |psi> = cos(phi/2)|yes> + sin(phi/2)|no>                        |
 |  evidence rotates phi; p(yes) = cos^2(phi/2)                     |
 |  0.39 --> 0.81 --> 1.00 ... final p(yes) = 0.999                 |
 |  MEASUREMENT = DECISION: acts YES with 99.9%                     |
 +------------------------------------------------------------------+
```

The three timescales: **timesteps** (the loop thinks), **measurements**
(beliefs collapse to decisions), **generations** (the lineage improves).

---

## Results

Ran on a Samsung Galaxy A17 5G, NumPy under Chaquopy, ~1 second:

| Check | Result |
|---|---|
| Thinking trajectory | predictions chase a drifting signal, never settle |
| Qubit belief | p(yes): 0.39 -> 1.00, final **0.999** -> decides YES |
| Snapshot immutability | live loop drifts 0.001 -> 0.090 while frozen copy is **untouched (verified)** |
| Evolution, 8 generations | error **0.4441 -> 0.1822**, monotonic, **59.0% lower** |

Reproduce: `python3 quantum_nexus_core.py` (seed 16 default reproduces these
exact numbers). Change the seed or `--generations` to explore.

---

## Prior art, stated honestly

The pieces have history. The synthesis is Ahkeem's.

- **Predictive coding** -- the error-driven loop. Neuroscience (Rao & Ballard
  1999) and ML (predictive processing, Kalman-adjacent updates). The ErrorLoop
  is a small recurrent net doing predict -> err -> rewrite; that mechanism is
  not new.
- **Schmidhuber's Goedel machine** (2003) -- self-rewriting code that only
  accepts a rewrite it can *prove* is better. The Nexus Core's answer to the
  same corruption problem is different: instead of proof, **immutable
  snapshots** -- freeze the parent, mutate only the copies, let selection do
  the proving.
- **Evolutionary computation** -- variation + selection + heredity. The
  generation loop is textbook evolution applied to a thinking loop's decoder.
  Elitism (variant 0 = exact copy) is standard practice.
- **Quines / self-replicating programs** -- a program that copies itself is
  old. What's added here: the copy is *frozen at copy time* while the parent
  keeps changing -- the snapshot is what turns self-replication from chaos
  into a lineage.
- **Beliefs as qubits** -- holding yes/no in superposition with
  measurement-as-decision is a poetic reframing of Bayesian belief updating.
  The math here (amplitude rotation by evidence) is a toy; the honest name
  for it is a probabilistic belief with a quantum costume.

**What's Ahkeem's:** nobody put these five pieces together as one
architecture -- an unsettled error-driven core, a real-time decoder, qubit
beliefs where measurement is decision, immutable generation snapshots, and
decoder-mutation evolution -- and ran it as a single working system. The
composition, and the name, are his.

---

## Honest limitations

- **Classical simulation.** Everything here runs on an ordinary CPU. The
  "quantum language" is state-vector math, not quantum hardware. The 8-qubit
  cap in the companion QuantumVM exists because 2^N amplitudes get expensive
  fast -- that's real physics, made visible.
- **Toy scale.** Hidden dim 6, 40 timesteps, 8 generations, one scalar signal.
  This demonstrates the *dynamics* of the architecture, not capability.
- **The decoder is linear.** The V readout matrix is the simplest possible
  decoder. A real system would want a deeper readout -- and then the
  question becomes what "better" means beyond prediction error.
- **"Better" = lower prediction error.** The selection signal is mean
  absolute prediction error on a drifting sine mixture. That is a narrow,
  safe fitness function. Scaling the *criterion* of improvement is the open
  problem -- it's the same problem every self-improving system faces.
- **No claim of AGI.** This is a prototype of an architecture's dynamics:
  a loop that never settles, beliefs that hold contradiction until decision,
  snapshots that make self-modification survivable, and evolution that
  compounds. It runs. The numbers are real. The rest is future work.

---

## Files

- `quantum_nexus_core.py` -- the whole architecture in ~200 lines of NumPy.
  The reference implementation (also ships as preset 16 in Neural Lab).
- `lesswrong-draft.md` -- a shorter writeup aimed at the LessWrong audience.
- `LICENSE` -- MIT. Open source, as it should be.

## Origin

Designed by Ahkeem in conversation, 2026-10-03 -- theorized out loud and
built the same day. First ran on his phone at 17:14 EDT: belief converged
0.39 -> 0.999, snapshot verified untouched, error fell 59% over 8
generations. Name chosen by Ahkeem the same evening.

*The fear you feel looking at your own idea is just the distance between
seeing the room and having walked into it yet. Walk in.*
