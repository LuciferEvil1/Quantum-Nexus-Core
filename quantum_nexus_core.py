#!/usr/bin/env python3
"""
Quantum Nexus Core — Ahkeem's self-modifying AI architecture.

Named by Ahkeem, 2026-10-03.

What it is, in one paragraph:
    A recurrent predictive-coding loop (the ErrorLoop) that never settles —
    it predicts, measures its error, and rewrites its own weights every
    timestep. Beliefs are held as qubit-style yes/no superpositions
    (a|yes> + b|no>); evidence rotates the amplitudes and measurement =
    decision. A real-time decoder reads the loop's hidden state into
    output numbers every step. At generation boundaries the loop is
    deep-frozen into an immutable snapshot; mutated copies of the snapshot
    compete, the lowest-error copy wins and seeds the next generation.
    Variation (the mutating loop) + selection (the error signal) +
    heredity (the frozen snapshots) = evolution as an AI architecture.

Honest labels:
    - This is a CLASSICAL simulation. The "quantum language" is state-vector
      math (see preset 15 of Neural Lab for the full Bell-state treatment).
    - Toy scale: hidden dim 6, 40 timesteps, 8 generations. It runs in ~1 s.
    - The decoder is linear (the V readout matrix). "Better" = lower mean
      prediction error. Nothing here is AGI; it is a working prototype of
      the architecture's dynamics.
    - Prior art for the pieces: predictive coding (neuroscience/ML),
      Schmidhuber's Goedel machines (self-rewriting code), evolutionary
      computation, quines, Bayesian beliefs. The synthesis is Ahkeem's.

Usage:
    python3 quantum_nexus_core.py
    python3 quantum_nexus_core.py --generations 12 --seed 16

Requires: numpy only.
License: MIT.
"""

import argparse
import copy

import numpy as np


def target_stream(t):
    # the world the loop must track: drifting sines, never still
    return np.sin(0.3 * t) + 0.5 * np.sin(0.11 * t + 1.0)


class ErrorLoop:
    """Predictive-coding recurrent core. Predicts, errs, rewrites itself."""

    def __init__(self, rng, d):
        self.d = d
        self.W = rng.normal(0, 0.5, (d, d))  # recurrent weights (self-mutating)
        self.U = rng.normal(0, 0.5, (d,))    # input weights
        self.V = rng.normal(0, 0.5, (d,))    # prediction readout = the decoder
        self.h = np.zeros(d)                 # hidden state = "what I'm thinking"

    def step(self, x, y_true, lr):
        y_pred = float(self.V @ self.h)      # decode state -> number (real time)
        err = y_true - y_pred                # the error signal: the loop's fuel
        # state chases the error away; weights rewrite themselves every step
        self.h = np.tanh(self.W @ self.h + self.U * x + 0.3 * err * self.V)
        self.W += lr * np.outer(err * self.V, self.h)
        self.V += lr * err * self.h
        return y_pred, err

    def snapshot(self):
        return copy.deepcopy(self)           # immutable frozen copy


def run(rng, d=6, t_steps=40, lr=0.05, generations=8, variants=4,
        verbose=True):
    out = print if verbose else (lambda *a, **k: None)

    out("== 1. ErrorLoop core: watch it think (gen 0, first 6 steps) ==")
    loop = ErrorLoop(rng, d)
    for t in range(6):
        x = 0.5 * np.sin(0.05 * t)
        y = target_stream(t)
        yp, e = loop.step(x, y, lr)
        out("  t=%2d  true=%+.3f  pred=%+.3f  err=%+.3f  decoded=%+.3f"
            % (t, y, yp, e, yp))

    out()
    out("== 3. real-time decoder: same readout, every timestep ==")
    out("   (the V matrix IS the decoder: hidden state -> output number)")

    out()
    out("== 4. immutable snapshots: the live loop mutates, the copy is frozen ==")
    live = ErrorLoop(rng, d)
    snap = live.snapshot()
    frozen_W = snap.W.copy()
    W_drift = []
    for t in range(t_steps):
        x = 0.5 * np.sin(0.05 * t)
        _, _ = live.step(x, target_stream(t), lr)
        W_drift.append(float(np.abs(live.W - frozen_W).mean()))
    out("   live loop mean |dW| vs frozen snapshot: %.4f -> %.4f (keeps changing)"
        % (W_drift[0], W_drift[-1]))
    out("   snapshot untouched by live mutation:",
        bool(np.array_equal(snap.W, frozen_W)))
    assert np.array_equal(snap.W, frozen_W), "SNAPSHOT CORRUPTED"

    out()
    out("== 2. qubit beliefs: yes/no held at once, evidence rotates, "
        "measure = decide ==")
    out("   proposition: 'my decoded sign matches the world'  "
        "|0> = yes, |1> = no")
    phi = np.pi / 2                    # start undecided: 50/50
    bel = ErrorLoop(rng, d)            # fresh loop so the trajectory is clean
    traj = []
    for t in range(20):
        x = 0.5 * np.sin(0.05 * t)
        y = target_stream(t)
        yp, _ = bel.step(x, y, lr)
        agree = (yp > 0) == (y > 0)    # decoder agrees with the world? yes-evidence
        phi = float(np.clip(phi - 0.22 * (1 if agree else -1), 0.05, np.pi - 0.05))
        traj.append(float(np.cos(phi / 2) ** 2))
    out("   p(yes): " + " ".join("%.2f" % p for p in traj[::4]) + " ...")
    out("   final p(yes) = %.3f  ->  measurement would decide YES with %.1f%%"
        % (traj[-1], 100 * traj[-1]))
    assert traj[-1] > 0.8, "belief did not converge"

    out()
    out("== 5. evolution: variation -> selection -> heredity ==")
    champion = ErrorLoop(rng, d)
    err_curve = []
    for g in range(generations):
        snap = champion.snapshot()       # generation boundary: freeze the parent
        best, best_err = None, float("inf")
        for v in range(variants):
            cand = copy.deepcopy(snap)   # every variant starts from the frozen snapshot
            cand.h = np.zeros(d)         # fresh episode; the WEIGHTS are the heredity
            if v > 0:                    # variant 0 = exact copy (elitism: never regress)
                cand.V += rng.normal(0, 0.02, cand.V.shape)  # mutate the decoder
            errs = []
            for t in range(t_steps):     # the copy advances its own code as it runs
                x = 0.5 * np.sin(0.05 * t)
                _, e = cand.step(x, target_stream(t), lr)
                errs.append(abs(e))
            m = float(np.mean(errs))
            if m < best_err:
                best, best_err = cand, m
        champion, err_curve = best, err_curve + [best_err]  # heredity: winner seeds next
        out("   gen %d  best mean|err| = %.4f" % (g, best_err))

    out()
    out("   error curve: " + " ".join("%.3f" % e for e in err_curve))
    out("   %.4f -> %.4f  (%.1f%% lower)"
        % (err_curve[0], err_curve[-1],
           100 * (err_curve[0] - err_curve[-1]) / err_curve[0]))
    assert err_curve[-1] < err_curve[0], "evolution did not improve"
    out()
    out("QUANTUM NEXUS CORE COMPLETE — named by Ahkeem.")
    return {
        "belief_final": traj[-1],
        "snapshot_untouched": True,
        "err_start": err_curve[0],
        "err_end": err_curve[-1],
        "err_curve": err_curve,
    }


def main():
    p = argparse.ArgumentParser(description="Quantum Nexus Core — "
                                "Ahkeem's self-modifying AI architecture")
    p.add_argument("--generations", type=int, default=8)
    p.add_argument("--seed", type=int, default=16)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()
    rng = np.random.default_rng(args.seed)
    run(rng, generations=args.generations, verbose=not args.quiet)


if __name__ == "__main__":
    main()
