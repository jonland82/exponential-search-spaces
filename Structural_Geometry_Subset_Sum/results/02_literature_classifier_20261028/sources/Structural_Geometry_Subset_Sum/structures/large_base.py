"""Bounded blind base discovery and exact aggregate-coordinate checks."""
from dataclasses import asdict, dataclass
from math import gcd

from Structural_Geometry_Subset_Sum.budget import CheckLimit, LocalMeter


@dataclass(frozen=True)
class Geometry:
    divisor: int
    base: int
    p: tuple[int, ...]
    r: tuple[int, ...]
    target: int
    r_min: int
    r_max: int
    q_low: int
    q_high: int

    @property
    def q_count(self):
        return max(0, self.q_high-self.q_low+1)

    @property
    def width(self):
        return self.r_max-self.r_min+1

    @property
    def dp_bits(self):
        return max(0, self.q_high+1)*self.width

    @property
    def history_bits(self):
        return (len(self.p)+1)*self.dp_bits

    def record(self):
        return dict(**asdict(self), q_count=self.q_count, dp_bits=self.dp_bits,
            history_bits=self.history_bits, relative_residual_width=(self.width-1)/self.base)


def candidates(weights, meter, maximum=24):
    """Fixed data-only candidates: powers of two and large observed gaps.

    Minimum/median weight, eight nearby powers of two (no generator metadata),
    then four largest gaps divided by 1..4. Duplicates removed, at most 24 bases.
    Discovery is a bounded heuristic, not minimum distance or lattice reduction.
    """
    n = len(weights)
    meter.tick(max(1, n*max(1, n.bit_length())))
    values = sorted(set(weights))
    if not values:
        return ()
    bits = values[-1].bit_length()
    proposed = [values[0], values[len(values)//2]]
    proposed += [1 << exponent for exponent in range(max(1, bits-1), max(0, bits-9), -1)]
    gaps = sorted({b-a for a, b in zip(values, values[1:])}, reverse=True)[:4]
    for gap in gaps:
        proposed += [(gap+k//2)//k for k in range(1, 5)]
    result = tuple(dict.fromkeys(value for value in proposed if value >= 2))[:maximum]
    meter.tick(len(proposed))
    return result


def describe(weights, target, base, divisor=1, meter=None):
    if type(base) is not int or base < 2 or type(divisor) is not int or divisor < 1:
        raise ValueError("base >= 2 and divisor >= 1 required")
    if type(target) is not int or target % divisor or any(type(w) is not int or w <= 0 or w % divisor for w in weights):
        raise ValueError("positive integer weights on the declared gcd grid required")
    p, r = [], []
    for weight in weights:
        if meter is not None:
            meter.tick(1)
        value = weight//divisor
        quotient = (value+base//2)//base
        p.append(quotient)
        r.append(value-base*quotient)
    low, high = sum(min(0, value) for value in r), sum(max(0, value) for value in r)
    t = target//divisor
    q_low = max(0, -((high-t)//base))
    q_high = min(sum(p), (t-low)//base)
    if meter is not None:
        meter.tick(4*len(weights)+8)
    return Geometry(divisor, base, tuple(p), tuple(r), t, low, high, q_low, q_high)


def detect(weights, target, meter, maximum=24):
    if not weights:
        return None, 0
    divisor = 0
    for value in weights:
        meter.tick()
        divisor = gcd(divisor, value)
    if target % divisor:
        return None, 0
    normalized = tuple(w//divisor for w in weights)
    meter.tick(len(weights))
    proposals = candidates(normalized, meter, maximum)
    best = None
    for base in proposals:
        candidate = describe(weights, target, base, divisor, meter)
        score = (candidate.q_count != 0, candidate.history_bits, candidate.width, candidate.base)
        if best is None or score < best[0]:
            best = score, candidate
    return (None if best is None else best[1]), len(proposals)


def eligible(geometry, *, max_dp_bits=2_000_000, max_history_bits=64_000_000,
             max_q_count=4, selective=False):
    if geometry is None:
        return False
    if geometry.q_count == 0:
        return True
    return (geometry.q_count <= (2 if selective else max_q_count)
        and geometry.dp_bits <= max_dp_bits and geometry.history_bits <= max_history_bits
        and (not selective or geometry.width-1 <= geometry.base))


def check(geometry, parent, *, max_work=12000, max_dp_bits=2_000_000,
          max_history_bits=64_000_000, max_q_count=4):
    """Exact two-coordinate subset sum; interrupted DP cannot certify NO."""
    meter = LocalMeter(parent, min(max_work, parent.remaining))
    updates, history = 0, []

    def finish(status, reason, witness=None, processed=0):
        meter.check()
        return dict(status=status, reason=reason, witness=witness, work=meter.work,
            updates=updates, processed=processed)

    if not eligible(geometry, max_dp_bits=max_dp_bits, max_history_bits=max_history_bits,
                    max_q_count=max_q_count):
        return finish("unresolved", "representation_cap")
    try:
        meter.tick()
        if geometry.q_count == 0:
            return finish("no", "aggregate_gap")
        width, maximum_q = geometry.width, geometry.q_high
        parent.peak_dp_bits = max(parent.peak_dp_bits, geometry.dp_bits)
        parent.peak_history_bits = max(parent.peak_history_bits, geometry.history_bits)
        mask = (1 << width)-1
        rows = [0]*(maximum_q+1)
        rows[0] = 1 << -geometry.r_min
        history.append(tuple(rows))
        prefix_p = 0
        for index, (p, r) in enumerate(zip(geometry.p, geometry.r)):
            meter.tick()
            prefix_p += p
            for q in range(min(maximum_q, prefix_p), p-1, -1):
                meter.tick()
                source = rows[q-p]
                rows[q] |= ((source << r) & mask) if r >= 0 else source >> -r
                updates += 1
            history.append(tuple(rows))
            for q in range(geometry.q_low, geometry.q_high+1):
                meter.tick()
                residual = geometry.target-geometry.base*q
                bit = residual-geometry.r_min
                if 0 <= bit < width and rows[q] >> bit & 1:
                    chosen, remaining_q, remaining_r = [], q, residual
                    for position in range(index, -1, -1):
                        meter.tick()
                        bit = remaining_r-geometry.r_min
                        if (0 <= remaining_q <= maximum_q and 0 <= bit < width
                                and history[position][remaining_q] >> bit & 1):
                            continue
                        chosen.append(position)
                        remaining_q -= geometry.p[position]
                        remaining_r -= geometry.r[position]
                    if remaining_q or remaining_r:
                        raise AssertionError("aggregate witness reconstruction failed")
                    return finish("yes", "aggregate_witness", tuple(sorted(chosen)), index+1)
        return finish("no", "aggregate_dp_exhausted", processed=len(geometry.p))
    except CheckLimit:
        return finish("unresolved", "check_work_limit", processed=len(history)-1)
