"""Smoke tests for the standalone Doxa package."""
import random

import doxa
from doxa import sos, stoqos
from doxa import domains as D
from doxa.cli import main


def test_three_valued_graphs():
    assert doxa.truth3(doxa.judge("radius <= diameter")) == "true"
    assert doxa.truth3(doxa.judge("diameter <= radius")) == "false"
    assert doxa.truth3(doxa.judge("foo <= bar")) == "unknown"


def test_means_is_proven_with_certificate():
    j = doxa.judge_domain(D._number_means_domain(), "geomean <= mean")
    assert j.verdict == "true" and j.certificate is not None
    assert "AM–GM" in j.certificate


def test_sos_sound_on_random_battery():
    F = D._number_means_domain().functionals
    names = list(F)
    rng = random.Random(3)
    battery = [[rng.randint(1, 40) for _ in range(rng.randint(3, 7))] for _ in range(1000)]
    vals = {n: [float(F[n](v)) for v in battery] for n in names}
    for a in names:
        for b in names:
            if a != b and sos.certify(a, b) is not None:
                assert all(vals[a][i] <= vals[b][i] + 1e-9 for i in range(len(battery)))


def test_model_covers_six_domains():
    assert doxa.evidence_model().meta["domains"] == \
        ["graphs", "sequences", "number_theory", "means", "triangles", "primes"]


def test_cli(capsys):
    assert main(["version"]) == 0
    assert "Doxa" in capsys.readouterr().out
    assert main(["realistic", "radius <= diameter"]) == 0
    assert "TRUE" in capsys.readouterr().out
    assert main(["realistic", "--domain", "means", "geomean <= mean"]) == 0
    assert "proof" in capsys.readouterr().out
