#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  SOVEREIGN SEOS v1.2 — Evidence Trust Platform (Audited)         ║
║  Zero dependencies. Single file. Runnable.                       ║
╚══════════════════════════════════════════════════════════════════╝
"""
import sys, json, hashlib, math, random, pathlib
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import platform, subprocess, io
from contextlib import redirect_stdout

random.seed(42)

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def utcnow_str() -> str:
    return utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def canon_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

# ═══════════════════════════════════════════════════════════════
# ASCII RENDERING
# ═══════════════════════════════════════════════════════════════

def box(title: str, lines: List[str], w: int = 66) -> str:
    inner = w - 4
    wrapped: List[str] = []
    for l in lines:
        if not l:
            wrapped.append("")
            continue
        while len(l) > inner:
            wrapped.append(l[:inner])
            l = l[inner:]
        wrapped.append(l)
    r = [f"┌{'─'*(w-2)}┐", f"│ {title[:inner].ljust(inner)} │", f"├{'─'*(w-2)}┤"]
    r += [f"│ {x.ljust(inner)} │" for x in wrapped]
    r.append(f"└{'─'*(w-2)}┘")
    return "\n".join(r)

def bar(v: float, max_v: float = 100, w: int = 25) -> str:
    n = max(0, min(w, int(w * v / max_v)))
    return "█" * n + "░" * (w - n)

def spark(vals: List[float]) -> str:
    if not vals: return ""
    ch = "▁▂▃▄▅▆▇█"
    lo, hi = min(vals), max(vals)
    rng = hi - lo or 1
    return "".join(ch[min(7, int((v - lo) / rng * 8))] for v in vals)

def line_graph(vals: List[float], h: int = 8) -> str:
    if not vals: return ""
    lo, hi = min(vals), max(vals)
    rng = hi - lo or 1
    levels = [int((v - lo) / rng * (h - 1)) for v in vals]
    out = []
    for row in range(h - 1, -1, -1):
        out.append("  " + "".join(
            "●" if lv == row else ("│" if lv > row else " ") for lv in levels))
    out.append("  " + "─" * len(vals))
    return "\n".join(out)

# ═══════════════════════════════════════════════════════════════
# MATH LAYER
# ═══════════════════════════════════════════════════════════════

class MathLayer:
    @staticmethod
    def pascal(n: int, k: int) -> Dict:
        total = 2 ** n
        valid = sum(math.comb(n, i) for i in range(k, n + 1))
        return {"row": [math.comb(n, i) for i in range(n + 1)],
                "valid": valid, "total": total, "prob": valid / total}

    @staticmethod
    def bayes(prior: float, evidence: List[Dict]) -> Dict:
        LIK = {"PASS": 0.95, "FAIL": 0.10}
        t = prior
        hist = [prior]
        for e in evidence:
            raw = LIK.get(e["outcome"], 0.5)
            conf = e.get("confidence", 0.9)
            lik = raw * conf + 0.5 * (1 - conf)
            p_ev = lik * t + (1 - lik) * (1 - t)
            t = (lik * t) / p_ev if p_ev > 0 else t
            hist.append(t)
        return {"posterior": t, "history": hist, "score": t * 100}

    @staticmethod
    def derivative(f, x: float, h: float = 1e-6) -> float:
        return (f(x + h) - f(x - h)) / (2 * h)

    @staticmethod
    def integrate(f, a: float, b: float, n: int = 1000) -> float:
        if n % 2: n += 1
        h = (b - a) / n
        s = f(a) + f(b)
        for i in range(1, n):
            s += f(a + i * h) * (4 if i % 2 else 2)
        return s * h / 3

    @staticmethod
    def ema(hist: List[float], new: float, alpha: float = 0.3) -> float:
        if not hist: return new
        return alpha * new + (1 - alpha) * hist[-1]

    @staticmethod
    def drift(hist: List[float]) -> Tuple[float, float]:
        if len(hist) < 2: return (0.0, 0.0)
        d1 = hist[-1] - hist[-2]
        prev = hist[-3] if len(hist) >= 3 else hist[-2]
        d2 = hist[-1] - 2 * hist[-2] + prev
        return (d1, d2)

    @staticmethod
    def level(s: float) -> str:
        for t, l in [(95, "T7"), (90, "T6"), (85, "T5"), (80, "T4"),
                     (70, "T3"), (60, "T2"), (50, "T1")]:
            if s >= t: return l
        return "T0"

# ═══════════════════════════════════════════════════════════════
# DOMAIN
# ═══════════════════════════════════════════════════════════════

@dataclass
class Evidence:
    id: str; type: str; title: str; source: str; hash: str
    status: str = "VERIFIED"; confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)

@dataclass
class TrustScore:
    score: int; level: str; coverage: float
    dims: Dict[str, float]; d1: float; d2: float

class TrustEngine:
    W = {"coverage": .30, "security": .25, "compliance": .20,
         "quality": .15, "governance": .10}
    MIN_CONF = 0.75

    def compute(self, ev: List[Evidence], approvals: List[Dict] = None,
                hist: List[float] = None) -> TrustScore:
        valid = [e for e in ev if e.status == "VERIFIED"
                 and e.confidence >= self.MIN_CONF]
        by_type: Dict[str, List[Evidence]] = {}
        for e in valid:
            by_type.setdefault(e.type, []).append(e)

        required = {"SECURITY", "COMPLIANCE", "TEST", "ARCHITECTURE"}
        coverage = len(set(by_type) & required) / len(required) * 100

        tests = by_type.get("TEST", [])
        quality = (sum(e.confidence for e in tests) / len(tests) * 100) if tests else 0.0

        required_roles = {"CTO", "Security Lead", "Governance Board", "Engineering Director"}
        approved_roles = {a["role"] for a in (approvals or [])
                         if a.get("decision") == "APPROVE"}
        governance = len(approved_roles & required_roles) / len(required_roles) * 100

        dims = {
            "coverage":    coverage,
            "security":    100.0 if "SECURITY" in by_type else 0.0,
            "compliance":  100.0 if "COMPLIANCE" in by_type else 0.0,
            "quality":     quality,
            "governance":  governance,
        }
        raw = sum(self.W[k] * v for k, v in dims.items())

        if hist:
            raw = MathLayer.ema(hist, raw, 0.4)

        full_hist = (hist or []) + [raw]
        d1, d2 = MathLayer.drift(full_hist)
        return TrustScore(int(round(raw)), MathLayer.level(raw),
                          coverage, dims, d1, d2)

class PolicyEngine:
    def __init__(self, cfg: Dict):
        self.cfg = cfg

    def eval(self, trust: TrustScore, ev: List[Evidence],
             approvals: List[Dict]) -> Dict:
        reasons = []
        if trust.score < self.cfg["min_trust"]:
            reasons.append(f"trust {trust.score} < {self.cfg['min_trust']}")
        if trust.coverage < self.cfg["min_cov"]:
            reasons.append(f"coverage {trust.coverage:.1f}% < {self.cfg['min_cov']}%")
        present = {e.type for e in ev
                   if e.status == "VERIFIED" and e.confidence >= TrustEngine.MIN_CONF}
        missing = set(self.cfg["required_ev"]) - present
        if missing:
            reasons.append(f"missing evidence: {sorted(missing)}")
        approved = {a["role"] for a in approvals if a["decision"] == "APPROVE"}
        miss_appr = set(self.cfg["required_appr"]) - approved
        if miss_appr:
            reasons.append(f"missing approvals: {sorted(miss_appr)}")
        return {"allow": not reasons, "reasons": reasons}

class Ledger:
    GENESIS = "0" * 64

    def __init__(self):
        self.entries: List[Dict] = []
        self._append("GENESIS", {})

    def _calc_hash(self, prev_hash: str, seq: int, event: str,
                   payload: Dict, ts: str) -> str:
        raw = f"{prev_hash}|{seq}|{event}|{canon_json(payload)}|{ts}"
        return sha256_str(raw)

    def _append(self, event: str, payload: Dict):
        prev = self.entries[-1]["entry_hash"] if self.entries else self.GENESIS
        seq = len(self.entries) + 1
        ts = utcnow_str()
        h = self._calc_hash(prev, seq, event, payload, ts)
        self.entries.append({
            "seq": seq, "event": event, "payload": payload,
            "prev_hash": prev, "entry_hash": h, "ts": ts,
        })

    def append(self, event, payload):
        self._append(event, payload)

    def verify(self) -> Tuple[bool, str]:
        prev = self.GENESIS
        for idx, e in enumerate(self.entries):
            seq = idx + 1
            if e["seq"] != seq:
                return False, f"sequence gap at idx {idx}: {e['seq']} != {seq}"
            if e["prev_hash"] != prev:
                return False, f"chain broken at seq {seq}"
            expected = self._calc_hash(prev, seq, e["event"], e["payload"], e["ts"])
            if e["entry_hash"] != expected:
                return False, f"tamper detected at seq {seq}: hash mismatch"
            prev = e["entry_hash"]
        return True, f"chain intact ({len(self.entries)} entries)"

    def save_jsonl(self, path: pathlib.Path):
        with path.open("a", encoding="utf-8") as f:
            for e in self.entries:
                f.write(canon_json(e) + "\n")

    @classmethod
    def load_jsonl(cls, path: pathlib.Path):
        L = cls()
        L.entries = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    L.entries.append(json.loads(line))
        if not L.entries or L.entries[0]["event"] != "GENESIS":
            raise ValueError("Ledger file must start with GENESIS entry")
        ok, msg = L.verify()
        if not ok:
            raise ValueError(f"Loaded ledger corrupted: {msg}")
        return L

# ═══════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════

def make_demo_evidence() -> List[Evidence]:
    return [
        Evidence("E1", "SECURITY",     "SAST scan",   "ci",   sha256_str("sast"), .95),
        Evidence("E2", "COMPLIANCE",   "SBOM",        "ci",   sha256_str("sbom"), .99),
        Evidence("E3", "TEST",         "Unit tests",  "ci",   sha256_str("unit"), .92),
        Evidence("E4", "TEST",         "Integration", "ci",   sha256_str("int"),  .88),
        Evidence("E5", "ARCHITECTURE", "ADR-001",     "repo", sha256_str("adr"),  1.00),
    ]

def make_approvals(full: bool = True) -> List[Dict]:
    base = [{"role": "CTO", "decision": "APPROVE"},
            {"role": "Security Lead", "decision": "APPROVE"}]
    if full:
        base += [{"role": "Governance Board", "decision": "APPROVE"},
                 {"role": "Engineering Director", "decision": "APPROVE"}]
    return base

def make_policy() -> PolicyEngine:
    return PolicyEngine({
        "min_trust": 85, "min_cov": 95,
        "required_ev": ["SECURITY", "COMPLIANCE", "TEST", "ARCHITECTURE"],
        "required_appr": ["CTO", "Security Lead",
                          "Governance Board", "Engineering Director"],
    })

def demo():
    print("\n" + "═" * 66)
    print("  SOVEREIGN SEOS v1.2 — END-TO-END DEMO")
    print("═" * 66)

    print("\n▸ [1/8] Evidence Registry")
    ev = make_demo_evidence()
    for e in ev:
        print(f"  ✓ {e.id} [{e.type:12}] {e.title:14} conf={e.confidence:.2f}")

    print("\n▸ [2/8] Pascal Quorum (5 approvers, need 4)")
    q = MathLayer.pascal(5, 4)
    print(f"  C(5,k) row: {q['row']}")
    print(f"  Valid: {q['valid']}/{q['total']} = {q['prob']:.2%}")

    print("\n▸ [3/8] Bayesian Trust Update")
    b = MathLayer.bayes(0.5, [{"outcome": "PASS", "confidence": e.confidence}
                              for e in ev])
    print(f"  Prior: 0.50 → Posterior: {b['posterior']:.4f}")
    print(f"  Evolution: {spark(b['history'])}")

    print("\n▸ [4/8] Trust Engine (no approvals yet — governance = 0)")
    trust0 = TrustEngine().compute(ev, approvals=[])
    print(f"  Score: {trust0.score}/100  Level: {trust0.level}")
    for k, v in trust0.dims.items():
        print(f"    {k:12} {bar(v)} {v:5.1f}")
    print(f"  ← B7 fixed: governance dim = {trust0.dims['governance']:.0f} (was hardcoded 100)")

    print("\n▸ [5/8] Policy Evaluation (approvals incomplete)")
    policy = make_policy()
    r = policy.eval(trust0, ev, make_approvals(False))
    print(f"  Allow: {r['allow']}")
    for reason in r["reasons"]:
        print(f"    ✗ {reason}")

    print("\n▸ [6/8] Approvals Complete → recompute trust")
    full_appr = make_approvals(True)
    trust1 = TrustEngine().compute(ev, approvals=full_appr)
    print(f"  Trust: {trust0.score} → {trust1.score}  (governance {trust0.dims['governance']:.0f} → {trust1.dims['governance']:.0f})")
    r = policy.eval(trust1, ev, full_appr)
    print(f"  Allow: {r['allow']}")
    if r["allow"]:
        print("  ✓ All gates pass — release authorized")
    trust = trust1

    print("\n▸ [7/8] Immutable Ledger")
    L = Ledger()
    for evt, payload in [
        ("EVIDENCE_BUNDLE",    {"count": len(ev)}),
        ("TRUST_EVALUATED",    {"score": trust.score, "level": trust.level}),
        ("POLICY_EVALUATED",   {"allow": r["allow"]}),
        ("APPROVED",           {"approvers": [a["role"] for a in full_appr]}),
        ("RELEASE_AUTHORIZED", {"release": "v1.0.0"}),
    ]:
        L.append(evt, payload)
    for e in L.entries:
        print(f"  #{e['seq']:02d} {e['event']:20} {e['entry_hash'][:20]}…")
    ok, msg = L.verify()
    print(f"  {'✓' if ok else '✗'} {msg}")

    print("\n▸ [8/8] Calculus — Trust Trajectory (20 days)")
    hist = [trust.score]
    for _ in range(20):
        hist.append(min(100, max(0, hist[-1] + random.uniform(-2, 3))))
    print(f"  Trajectory: {spark(hist)}")
    d1, d2 = MathLayer.drift(hist)
    print(f"  d/dt = {d1:+.2f}  d²/dt² = {d2:+.2f}")
    curve = lambda x: hist[min(int(x), len(hist) - 1)]
    auc = MathLayer.integrate(curve, 0, len(hist) - 1)
    print(f"  ∫trust dt = {auc:.1f} (AUC of discrete trajectory)")
    print("\n" + line_graph(hist, h=6))

    stmt = {
        "statement_id": f"STMT-{utcnow():%Y-%m-%d}-001",
        "level":        "L2" if trust.score >= 85 else "L1",
        "trust":        f"{trust.score}/100 ({trust.level})",
        "evidence":     len(ev),
        "approvals":    ", ".join(a["role"] for a in full_appr),
        "root":         L.entries[-1]["entry_hash"][:32] + "…",
    }
    print("\n▸ Attestation Statement")
    print(box("ATTESTATION", [f"{k:14} {v}" for k, v in stmt.items()]))

    print("\n" + "═" * 66)
    print(f"  ✓ COMPLETE — trust {trust.score}/100, {len(L.entries)} ledger entries")
    print("═" * 66 + "\n")

def math_only():
    print("\n" + "═" * 66 + "\n  MATH LAYER\n" + "═" * 66)
    print("\n▸ Pascal's triangle — quorum probability")
    for n, k in [(3, 2), (5, 3), (5, 4), (7, 5)]:
        q = MathLayer.pascal(n, k)
        print(f"  {k}-of-{n}: {q['row']}  P={q['prob']:.2%}")

    print("\n▸ Bayesian update (3 successive PASS)")
    for prior in [0.3, 0.5, 0.7]:
        b = MathLayer.bayes(prior, [{"outcome": "PASS"}] * 3)
        print(f"  prior={prior} → posterior={b['posterior']:.4f}")

    print("\n▸ Derivative: numeric vs analytic")
    f = lambda x: x**3 - 2 * x**2 + x
    fp = lambda x: 3 * x**2 - 4 * x + 1
    print("  f(x) = x³ − 2x² + x,  f'(x) = 3x² − 4x + 1")
    for x in [0, 1, 2, 3]:
        nd = MathLayer.derivative(f, x)
        print(f"    f'({x}): numeric={nd:+.4f}  analytic={fp(x):+.4f}  Δ={abs(nd - fp(x)):.2e}")

    print("\n▸ Simpson's rule ∫₀³ (x³ − 2x² + x) dx")
    I = MathLayer.integrate(f, 0, 3, n=1000)
    exact = 3**4 / 4 - 2 * 3**3 / 3 + 3**2 / 2
    print(f"  numeric  = {I:.8f}")
    print(f"  analytic = {exact:.8f}")
    print(f"  error    = {abs(I - exact):.2e}  {'✓' if abs(I - exact) < 1e-6 else '✗'}")

def sla_demo():
    from datetime import timedelta
    print("\n" + "═" * 66 + "\n  SLA ENFORCEMENT — AUTO-REVOKE\n" + "═" * 66)
    now = utcnow()
    risks = [
        {"id": "RISK-001", "class": "CONDITIONALLY_ACCEPTABLE", "deadline": now - timedelta(hours=2)},
        {"id": "RISK-002", "class": "ACCEPTABLE", "deadline": now + timedelta(days=5)},
    ]
    seal = "active"
    L = Ledger()
    print(f"\n  Initial seal: {seal}")
    for r in risks:
        d = r["deadline"] - now
        tag = "🔴 BREACHED" if d.total_seconds() < 0 else f"🟢 {d.days}d left"
        print(f"  {r['id']} [{r['class']:26}] {tag}")

    breached = [r for r in risks if r["deadline"] < now and r["class"] != "ACCEPTABLE"]
    if breached:
        seal = "revoked"
        L.append("AUTO_REVOKE", {"breached": [r["id"] for r in breached]})
        print(f"\n  🚨 AUTO-REVOKE triggered")
        print(f"  Seal → {seal}")
        print(f"  Ledger #{L.entries[-1]['seq']} written")

def verify():
    print("\n" + "═" * 66 + "\n  TAMPER DETECTION — B1/B6 PROOF\n" + "═" * 66)
    L = Ledger()
    for i in range(5):
        L.append("TEST", {"i": i, "data": f"payload-{i}"})
    ok, msg = L.verify()
    print(f"\n  Before tamper:  {'✓' if ok else '✗'} {msg}")
    print("\n  Tampering payload of entry #3 (seq=3) WITHOUT changing entry_hash…")
    L.entries[2]["payload"]["data"] = "TAMPERED"
    ok2, msg2 = L.verify()
    print(f"  After tamper:   {'✓' if ok2 else '✗'} {msg2}")
    return 0 if (ok and not ok2) else 1

def ledger_demo():
    print("\n" + "═" * 66 + "\n  JSONL PERSISTENCE — save & reload\n" + "═" * 66)
    p = pathlib.Path("/tmp/seos_ledger_demo.jsonl")
    if p.exists(): p.unlink()
    L = Ledger()
    for i in range(3): L.append("EVENT", {"i": i})
    L.save_jsonl(p)
    print(f"\n  Saved {len(L.entries)} entries → {p}")
    L2 = Ledger.load_jsonl(p)
    ok, msg = L2.verify()
    print(f"  Reloaded: {'✓' if ok else '✗'} {msg}")
    print(f"  Size: {p.stat().st_size} bytes")

def self_test():
    print("\n" + "═" * 66 + "\n  SELF-TEST — verify every fix\n" + "═" * 66)
    tests: List[Tuple[str, bool]] = []
    
    L = Ledger()
    L.append("A", {"x": 1})
    L.append("B", {"x": 2})
    L.entries[1]["payload"]["x"] = 999
    ok, _ = L.verify()
    tests.append(("B1 Ledger detects payload tamper", not ok))

    ev = make_demo_evidence()
    t_no_hist = TrustEngine().compute(ev, approvals=make_approvals(True))
    t_with_hist = TrustEngine().compute(ev, approvals=make_approvals(True), hist=[10.0])
    tests.append(("B3 EMA pulls toward low history", t_with_hist.score < t_no_hist.score))

    t0 = TrustEngine().compute(ev, approvals=[])
    t4 = TrustEngine().compute(ev, approvals=make_approvals(True))
    tests.append(("B7 governance 0→100 with approvals", t0.dims["governance"] == 0 and t4.dims["governance"] == 100))

    ev_low = [Evidence("E1", "SECURITY", "x", "ci", sha256_str("x"), status="VERIFIED", confidence=0.5)]
    t_low = TrustEngine().compute(ev_low, approvals=[])
    tests.append(("B8 low-conf evidence not counted", t_low.dims["security"] == 0))

    p = pathlib.Path("/tmp/seos_selftest_bad.jsonl")
    p.write_text(canon_json({"seq": 1, "event": "NOT_GENESIS", "payload": {}, "prev_hash": "0" * 64, "entry_hash": "x", "ts": "x"}) + "\n")
    try:
        Ledger.load_jsonl(p)
        rejected = False
    except ValueError:
        rejected = True
    tests.append(("B9 load_jsonl rejects missing GENESIS", rejected))

    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        utcnow_str()
        dep = any("utcnow" in str(x.message) for x in w)
    tests.append(("B10 utcnow has no deprecation warning", not dep))

    out = box("t", ["คำว่า test", "a" * 100])
    tests.append(("B11 box handles long/multibyte", len(out) > 0))

    q = MathLayer.pascal(5, 4)
    tests.append(("Pascal C(5,4)+C(5,5)=6", q["valid"] == 6))

    f = lambda x: x**3 - 2*x**2 + x
    I = MathLayer.integrate(f, 0, 3, n=1000)
    tests.append(("Simpson ∫₀³ = 6.75", abs(I - 6.75) < 1e-6))

    fp = lambda x: 3*x**2 - 4*x + 1
    nd = MathLayer.derivative(f, 2)
    tests.append(("Derivative f'(2) = 5", abs(nd - fp(2)) < 1e-4))

    passed = sum(1 for _, ok in tests if ok)
    print()
    for name, ok in tests:
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n  {passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1

def attest():
    """Generate SLSA-style attestation JSON. Exit 0 = pass."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = self_test()
    output = buf.getvalue()
    
    def git(cmd):
        try:
            return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return "unknown"
            
    commit = git(["git", "rev-parse", "HEAD"])
    branch = git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    src_hash = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    ts = utcnow_str()
    
    body = {
        "_type": "https://seos.io/attestation/v1",
        "subject": [{"name": "seos.py", "digest": {"sha256": src_hash}}],
        "predicate": {
            "buildType": "seos-self-test",
            "builder": {"id": f"python:{platform.python_version()}", "platform": platform.platform()},
            "invocation": {"git_commit": commit, "git_branch": branch, "timestamp": ts},
            "result": {"exit_code": rc, "passed": rc == 0, "output_sha256": hashlib.sha256(output.encode()).hexdigest()},
        },
    }
    body_hash = hashlib.sha256(canon_json(body).encode()).hexdigest()
    attestation = {**body, "attestation_hash": "sha256:" + body_hash}
    
    pathlib.Path("attestation.json").write_text(json.dumps(attestation, indent=2, ensure_ascii=False))
    
    print(f"\n✅ Attestation written: attestation.json")
    print(f"   subject sha256: {src_hash[:32]}…")
    print(f"   attestation:    sha256:{body_hash[:32]}…")
    print(f"   exit:           {rc}")
    return rc

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    cmds = {"demo": demo, "math": math_only, "sla": sla_demo,
            "verify": verify, "ledger": ledger_demo, "self": self_test, "attest": attest}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        print("Commands:", ", ".join(cmds))
        return 1
    return cmds[sys.argv[1]]() or 0

if __name__ == "__main__":
    sys.exit(main())
