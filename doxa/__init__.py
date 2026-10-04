"""Doxa — a calibrated, honest judge for mathematical statements.

Doxa answers a bound ``a <= b`` in three-valued logic: **TRUE** (proven),
**FALSE** (a counterexample exists), or **REALISTIC** (holds on the evidence, but
unproven) — plus **UNKNOWN** when it cannot judge at all. It *scores* the plausible
middle and *proves* where it can (the means domain, via sum-of-squares
certificates). It never fakes certainty; only a proof or a counterexample moves a
claim off REALISTIC.

Greek ``δόξα`` — "plausible belief", the counterpart to ``epistēmē`` (proven
knowledge). Doxa is the model inside MatyOS; MatyOS owns the proof.
"""
__version__ = "0.40.0"

from doxa.stoqos import (judge, judge_domain, truth3, realistic_score,
                         score_evidence, Judgement, evidence_model)
from doxa import sos, stoqos, domains

__all__ = [
    "judge",            # typed verdict for one claim (true/realistic/false/unknown)
    "judge_domain",     # same, for a bound in any Domain (means, primes, triangles…)
    "truth3",           # collapse a Judgement to true/false/realistic/unknown
    "realistic_score",  # calibrated P(true) for a graph-inequality bound
    "score_evidence",   # domain-general REALISTIC score from evidence alone
    "evidence_model",   # the shipped calibrated model
    "Judgement",
    "sos",              # sound certificate engine (proves means inequalities)
    "stoqos", "domains",
    "__version__",
]
