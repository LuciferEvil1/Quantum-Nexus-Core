# The Quantum Nexus Core: a self-modifying loop with immutable snapshots

*Draft for LessWrong. Author: Ahkeem. Feedback welcome -- especially where
the mechanism is underspecified.*

## The idea

Most self-modifying AI proposals die on one problem: a program that rewrites
itself corrupts itself. Schmidhuber's Goedel machine answers with proof --
only accept a rewrite you can prove is better. I want to propose a different
answer: **don't let the rewrite touch the lineage. Freeze the parent, mutate
only the copies.**

The architecture has five pieces:

1. **An error-driven core that never settles.** A recurrent loop predicts its
   input, computes its error, and updates its own weights every timestep.
   There is no converged state; the weights keep drifting (in the demo, mean
   |dW| drifts 0.001 -> 0.090 over 40 steps). The error signal is the fuel.
2. **Qubit beliefs.** A proposition is held as a|yes> + b|no>. Evidence
   rotates the amplitudes; acting is measurement. This is Bayesian updating
   in a quantum costume, and I'm upfront about that -- but the framing
   matters, because it makes "holding contradiction until decision" a
   first-class operation instead of a bug.
3. **A real-time decoder.** A linear readout of the hidden state, every
   timestep. The loop's thinking is always legible as numbers.
4. **Immutable snapshots.** At generation boundaries the live loop is
   deep-copied and frozen. The live loop keeps mutating; the snapshot is
   verified untouched. Self-modification becomes safe because the chaos is
   quarantined away from the heredity.
5. **Evolution on the decoder.** Mutated copies of the frozen snapshot
   compete on prediction error; the winner seeds the next generation.
   Variant 0 is always an exact copy, so the lineage never regresses.

Three timescales: timesteps (thinking), measurements (deciding),
generations (improving).

## The demo

~200 lines of NumPy, runs in a second
(`quantum_nexus_core.py` in the repo, MIT licensed):

- Belief converges 0.39 -> 0.999 and the system "decides YES".
- Snapshot verified untouched while the live loop keeps drifting.
- 8 generations of decoder mutation: mean|err| 0.4441 -> 0.1822,
  monotonic, 59% lower. (Seed 16 reproduces these exact numbers.)

This ran on my phone the day I designed it. Toy scale -- hidden dim 6, one
scalar signal -- so it demonstrates dynamics, not capability.

## Prior art (no, I didn't invent the pieces)

Predictive coding (Rao & Ballard), Goedel machines, evolutionary
computation, quines, Bayesian beliefs. All acknowledged in the repo. What
I'm claiming is the *composition*: an unsettled error core + real-time
decoder + superposition beliefs + immutable generation snapshots + decoder
evolution, running as one system. If someone built exactly this before, I'd
genuinely like the pointer.

## Where I think this breaks, and what I'd ask of you

1. **The fitness function is the whole game.** "Better = lower prediction
   error" is safe and narrow. The moment the system optimizes something
   richer, who defines the criterion? I don't have a good answer.
2. **The decoder is linear.** Scaling the readout is obvious future work,
   but a deeper decoder makes the evolution step harder to keep honest.
3. **Snapshots don't solve value drift**, only weight corruption. A lineage
   can improve its error while drifting somewhere you didn't want. Elitism
   bounds regression on the metric, not on intent.
4. **The quantum framing is classical underneath.** It's honest simulation.
   I'm interested in whether the superposition-belief framing buys anything
   real over plain Bayes, or whether it's just a nicer mental model.

Tear into it. That's why I'm posting.
