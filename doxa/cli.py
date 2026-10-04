"""The ``doxa`` command line — judge a bound ``a <= b`` in three-valued logic."""
import sys

from doxa import __version__

USAGE = """doxa <command> [args]

Commands:
  realistic <claim>   judge "a <= b" as TRUE / FALSE / REALISTIC (or UNKNOWN)
                      [--domain <name>]  judge in a domain (means, primes, triangles, …)
                      [--batch <file>]   judge every claim in a file (one per line)
                      [--json]           machine-readable output
  ui [port]           launch the local web UI (default http://localhost:8000/doxa)
  version             print the Doxa version
  help                show this help

Examples:
  doxa realistic "radius <= diameter"
  doxa realistic --domain means "geomean <= mean"     # proven TRUE, with a proof
  doxa realistic --domain primes "next_prime <= twice_prime"
"""

# TRUE means proven (a certificate or a known theorem); REALISTIC is the middle
# value (held on evidence, unproven); FALSE has a counterexample; UNKNOWN can't be judged.
_TRUTH_LINE = {
    "true":      "TRUE        proven (a certificate or a known theorem)",
    "realistic": "REALISTIC   holds on all evidence, but unproven",
    "false":     "FALSE       a counterexample exists in the evidence",
    "unknown":   "UNKNOWN     cannot be judged (out of domain / unparseable)",
}


def _judge(claim, domain):
    from doxa import stoqos
    if domain and domain != "graphs":
        from doxa import domains as D
        doms = {d.name: d for d in D.all_domains()}
        if domain not in doms:
            print(f"doxa: unknown domain '{domain}'. Available: "
                  f"{', '.join(sorted(doms))}", file=sys.stderr)
            return None, None
        return stoqos.judge_domain(doms[domain], claim), stoqos
    return stoqos.judge(claim), stoqos


def _realistic(claim, as_json=False, domain=None):
    j, stoqos = _judge(claim, domain)
    if j is None:
        return 2
    truth = stoqos.truth3(j)
    if as_json:
        import json
        print(json.dumps({"claim": claim, "truth": truth, "verdict": j.verdict,
                          "value": j.value, "confidence": j.confidence,
                          "known": j.known, "note": j.note,
                          "certificate": j.certificate}, indent=2))
        return 0
    print(f"claim:    {claim}")
    print(f"verdict:  {_TRUTH_LINE.get(truth, truth)}")
    if truth == "realistic" and j.value is not None:
        print(f"value:    P(true) = {j.value:.2f}  (calibrated, confidence {j.confidence:.2f})")
    if j.certificate:
        print(f"proof:    {j.certificate}")
    print(f"note:     {j.note}")
    return 0


def _realistic_batch(path, as_json=False, domain=None):
    from doxa import stoqos
    try:
        with open(path, encoding="utf-8") as f:
            claims = [ln.strip() for ln in f
                      if ln.strip() and not ln.lstrip().startswith("#")]
    except OSError as e:
        print(f"doxa: cannot read {path}: {e}", file=sys.stderr)
        return 2
    if not claims:
        print(f"doxa: no claims in {path}", file=sys.stderr)
        return 2
    dom = None if not domain or domain == "graphs" else domain
    results = stoqos.judge_many(claims, domain=dom)
    if as_json:
        import json
        print(json.dumps([{"claim": c, "truth": stoqos.truth3(j), "value": j.value}
                          for c, j in zip(claims, results)], indent=2))
        return 0
    width = min(max((len(c) for c in claims), default=10), 48)
    for c, j in zip(claims, results):
        t = stoqos.truth3(j)
        tag = t.upper()
        if t == "realistic" and j.value is not None:
            tag += f"  {j.value:.2f}"
        print(f"{c[:width]:<{width}}  {tag}")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(USAGE)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in ("version", "--version", "-v"):
        print(f"Doxa {__version__}")
        return 0
    if cmd in ("help", "--help", "-h"):
        print(USAGE)
        return 0
    if cmd == "ui":
        from doxa.web import serve
        port = next((int(a) for a in rest if a.isdigit()), 8000)
        serve(port=port)
        return 0
    if cmd == "realistic":
        as_json = "--json" in rest
        rest = [a for a in rest if a != "--json"]
        domain = batch = None
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "--domain" and i + 1 < len(rest):
                domain = rest[i + 1]; rest = rest[:i] + rest[i + 2:]; continue
            if a.startswith("--domain="):
                domain = a.split("=", 1)[1]; rest = rest[:i] + rest[i + 1:]; continue
            if a == "--batch" and i + 1 < len(rest):
                batch = rest[i + 1]; rest = rest[:i] + rest[i + 2:]; continue
            if a.startswith("--batch="):
                batch = a.split("=", 1)[1]; rest = rest[:i] + rest[i + 1:]; continue
            i += 1
        if batch:
            return _realistic_batch(batch, as_json=as_json, domain=domain)
        if not rest:
            print('doxa: \'realistic\' needs a claim, e.g. doxa realistic "radius <= diameter"',
                  file=sys.stderr)
            return 2
        return _realistic(" ".join(rest), as_json=as_json, domain=domain)
    print(f"doxa: unknown command '{cmd}'. Try 'doxa help'.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
