"""One exact aggregate/residual core table, queried by bounded exceptions."""
from dataclasses import asdict, dataclass

from Structural_Geometry_Subset_Sum.budget import CheckLimit, LocalMeter


@dataclass(frozen=True)
class CorePlan:
    core: tuple[int, ...]
    exceptions: tuple[int, ...]
    r_min: int
    r_max: int
    maximum_q: int
    width: int
    dp_bits: int
    history_bits: int
    estimated_work: int

    def record(self):
        return asdict(self)


def choose_core(geometry, meter, *, available_work, maximum_exceptions=9,
                max_dp_bits=2_000_000, max_history_bits=64_000_000):
    """Trim largest absolute residuals; first partition fitting all declared gates.

    The base and gcd grid come from blind discovery, never planted metadata.
    Positive exceptional weights only decrease shifted targets, so one q range
    capped using the original target suffices for every exceptional assignment.
    """
    if geometry is None:
        return None
    n = len(geometry.p)
    meter.tick(max(1, n*max(1, n.bit_length())))
    ranked = sorted(range(n), key=lambda i:(-abs(geometry.r[i]), i))
    for count in range(min(n, maximum_exceptions)+1):
        meter.tick(4*n+8)
        exceptions = tuple(ranked[:count])
        removed = set(exceptions)
        core = tuple(i for i in range(n) if i not in removed)
        r_min = sum(min(0, geometry.r[i]) for i in core)
        r_max = sum(max(0, geometry.r[i]) for i in core)
        width = r_max-r_min+1
        maximum_q = min(sum(geometry.p[i] for i in core),
                        (geometry.target-r_min)//geometry.base)
        if maximum_q < 0:
            continue
        height = maximum_q+1
        area, history = height*width, (len(core)+1)*height*width
        # Count allocation, each row update and prefix-history reference copy.
        estimate, prefix = height+2+len(core), 0
        for i in core:
            prefix += geometry.p[i]
            limit = min(maximum_q, prefix)
            estimate += 1+max(0, limit-geometry.p[i]+1)+(limit+1)
        maximum_queries = min(height, (width-1)//geometry.base+1)
        estimate += (1 << count)*(5+maximum_queries)+3*n+4
        allowance = available_work() if callable(available_work) else available_work
        if area <= max_dp_bits and history <= max_history_bits and estimate <= allowance:
            return CorePlan(core, exceptions, r_min, r_max, maximum_q, width,
                            area, history, estimate)
    return None


def solve_core(geometry, plan, parent, *, max_work):
    """Exact YES/NO only after complete table construction and required queries."""
    meter = LocalMeter(parent, min(max_work, parent.remaining))
    built, updates, assignments, queries, histories = 0, 0, 0, 0, []

    def finish(status, reason, witness=None):
        meter.check()
        return dict(status=status, reason=reason, witness=witness, work=meter.work,
            core_builds=built, row_updates=updates, assignments=assignments,
            point_queries=queries, total_assignments=1 << len(plan.exceptions))

    try:
        height, width = plan.maximum_q+1, plan.width
        meter.tick(height+2)
        rows = [0]*height
        rows[0] = 1 << -plan.r_min
        mask = (1 << width)-1
        histories.append((rows[0],))
        prefix = 0
        parent.peak_dp_bits = max(parent.peak_dp_bits, plan.dp_bits)
        parent.peak_history_bits = max(parent.peak_history_bits, plan.history_bits)
        for index in plan.core:
            meter.tick()
            p, r = geometry.p[index], geometry.r[index]
            prefix += p
            upper = min(plan.maximum_q, prefix)
            for q in range(upper, p-1, -1):
                meter.tick()
                source = rows[q-p]
                rows[q] |= ((source << r) & mask) if r >= 0 else source >> -r
                updates += 1
            meter.tick(upper+1)
            histories.append(tuple(rows[:upper+1]))
        built = 1
        meter.tick(len(plan.core))
        core_total = sum(geometry.base*geometry.p[i]+geometry.r[i] for i in plan.core)
        exceptional_sum, previous_gray = 0, 0
        for step in range(1 << len(plan.exceptions)):
            meter.tick(5)
            gray = step ^ (step >> 1)
            if step:
                changed = gray ^ previous_gray
                offset = changed.bit_length()-1
                index = plan.exceptions[offset]
                weight = geometry.base*geometry.p[index]+geometry.r[index]
                exceptional_sum += weight if gray & changed else -weight
            previous_gray = gray
            assignments += 1
            target = geometry.target-exceptional_sum
            if target < 0 or target > core_total:
                continue
            low = max(0, (target-plan.r_max+geometry.base-1)//geometry.base)
            high = min(plan.maximum_q, (target-plan.r_min)//geometry.base)
            for q in range(low, high+1):
                meter.tick()
                queries += 1
                residual = target-geometry.base*q
                bit = residual-plan.r_min
                if not (0 <= bit < width and rows[q] >> bit & 1):
                    continue
                meter.tick(3*len(geometry.p)+4)
                chosen = [i for j, i in enumerate(plan.exceptions) if gray >> j & 1]
                remaining_q, remaining_r = q, residual
                for position in range(len(plan.core)-1, -1, -1):
                    old = histories[position]
                    bit = remaining_r-plan.r_min
                    if (0 <= remaining_q < len(old) and 0 <= bit < width
                            and old[remaining_q] >> bit & 1):
                        continue
                    index = plan.core[position]
                    chosen.append(index)
                    remaining_q -= geometry.p[index]
                    remaining_r -= geometry.r[index]
                if remaining_q or remaining_r:
                    raise AssertionError("exception-core reconstruction failed")
                return finish("yes", "exception_core_witness", tuple(sorted(chosen)))
        return finish("no", "exception_assignments_exhausted")
    except CheckLimit:
        return finish("unresolved", "exception_core_work_limit")
