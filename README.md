# Doxa

**A calibrated, honest judge for mathematical statements.**

Doxa answers a bound `a ≤ b` in three-valued logic:

- **TRUE** — proven (a certificate or a known theorem)
- **FALSE** — a counterexample exists in the evidence
- **REALISTIC** — holds on the evidence, but unproven (with a calibrated probability)
- **UNKNOWN** — it cannot be judged, and says so

It *scores* the plausible middle and *proves* where it can. It never fakes
certainty: only a proof or a counterexample moves a claim off REALISTIC.

> Greek *δόξα* — "plausible belief", the counterpart to *epistēmē* (proven
> knowledge). Doxa is the model; the kernel owns the proof.

Zero runtime dependencies (Python standard library only).

## Install

```bash
pip install doxa        # or: pipx install doxa
```

## Use

```bash
doxa realistic "radius <= diameter"                    # → TRUE (a known theorem)
doxa realistic "diameter <= radius"                    # → FALSE (counterexample)
doxa realistic --domain means "geomean <= mean"        # → TRUE, with a proof
doxa realistic --domain primes "next_prime <= twice_prime"   # Bertrand → REALISTIC
doxa realistic --batch claims.txt                      # judge many at once
doxa ui                                                # web UI at localhost:8000/doxa
```

```python
import doxa
doxa.truth3(doxa.judge("radius <= diameter"))          # "true"

from doxa import domains
j = doxa.judge_domain(domains._number_means_domain(), "geomean <= mean")
j.verdict       # "true"
j.certificate   # "power-mean inequality: M_{0} ≤ M_{1}  ·  SOS: AM–GM: (√a−√b)² ≥ 0"
```

## How it works

- **Scoring** — a small calibrated MLP reads evidence features (tightness,
  margins, correlation) of a bound over a weak battery and returns `P(true)`.
  It abstains when unsure rather than guess.
- **Proving (means domain)** — the means functionals are power means
  (`vmin = M₋∞ … vmax = M₊∞`), so a **sound** certificate engine
  (`doxa.sos`) settles every bound with the power-mean inequality, explicit
  **sum-of-squares** witnesses, order statistics and positivity — promoting
  REALISTIC → TRUE with the proof attached.
- **Domains** — graphs, sequences, number theory, means, triangles, primes.

The scorer sits at an honest ~0.8 AUC ceiling on the uncertain middle (evidence
cannot decide universal truth); truth comes from proof, not from the score. Doxa
is the model inside [MatyOS](https://github.com/MatyOS-Project/MatyOS).
