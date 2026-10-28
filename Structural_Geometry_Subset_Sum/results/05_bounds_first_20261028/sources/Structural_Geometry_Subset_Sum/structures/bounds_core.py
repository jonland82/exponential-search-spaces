"""Bounded partition discovery and exact bounds before optional core construction."""
from Structural_Geometry_Subset_Sum.budget import CheckLimit, LocalMeter
from Structural_Geometry_Subset_Sum.structures.exception_core import CorePlan


def choose_fast(geometry, parent, *, max_work, available_work, maximum_exceptions=9,
                max_dp_bits=2_000_000, max_history_bits=64_000_000):
    """Same residual ranking and first-fitting gates; cheap rejected partitions.

    Maintain residual/quotient totals as weights leave the core. Calculate the
    row/history work estimate only after the memory gates pass. The local cap
    can stop discovery without exhausting the shared fallback budget.
    """
    meter = LocalMeter(parent, min(max_work, parent.remaining))
    examined = 0

    def finish(plan, reason):
        meter.check()
        return plan, dict(work=meter.work, cap=max_work, examined=examined, reason=reason)

    if geometry is None:
        return finish(None, "no_geometry")
    try:
        n = len(geometry.p)
        meter.tick(max(1, n*max(1, n.bit_length())) + 4*n)
        ranked = sorted(range(n), key=lambda i:(-abs(geometry.r[i]), i))
        low = sum(min(0, r) for r in geometry.r)
        high = sum(max(0, r) for r in geometry.r)
        total_q = sum(geometry.p)
        removed = set()
        for count in range(min(n, maximum_exceptions)+1):
            meter.tick(8)
            examined += 1
            if count:
                i = ranked[count-1]
                removed.add(i)
                low -= min(0, geometry.r[i])
                high -= max(0, geometry.r[i])
                total_q -= geometry.p[i]
            maximum_q = min(total_q, (geometry.target-low)//geometry.base)
            if maximum_q < 0:
                continue
            width, height = high-low+1, maximum_q+1
            area, history = height*width, (n-count+1)*height*width
            if area > max_dp_bits or history > max_history_bits:
                continue
            meter.tick(3*n)
            core = tuple(i for i in range(n) if i not in removed)
            estimate, prefix = height+2+len(core), 0
            for i in core:
                prefix += geometry.p[i]
                upper = min(maximum_q, prefix)
                estimate += 1+max(0, upper-geometry.p[i]+1)+(upper+1)
            queries = min(height, (width-1)//geometry.base+1)
            estimate += (1 << count)*(5+queries)+3*n+4
            allowance = available_work() if callable(available_work) else available_work
            if estimate <= allowance:
                return finish(CorePlan(core, tuple(ranked[:count]), low, high,
                    maximum_q, width, area, history, estimate), "selected")
        return finish(None, "no_affordable_plan")
    except CheckLimit:
        return finish(None, "discovery_cap")


def solve_bounds(geometry, plan, parent, *, max_work, mode):
    """Bounds-only, eager DP, or one lazily built DP; all exact work is charged.

    Interval feasibility is necessary, never sufficient for a YES answer.
    Bounds-only stops unresolved at its first feasible assignment. A bounds NO
    requires checking every assignment and finding all projected intervals empty.
    """
    if mode not in ("bounds_only", "bounds_first", "fast_eager"):
        raise ValueError("unknown bounds mode")
    meter = LocalMeter(parent, min(max_work, parent.remaining))
    built = updates = assignments = queries = rejected = feasible = 0
    histories, rows = [], None

    def finish(status, reason, witness=None):
        meter.check()
        return dict(status=status, reason=reason, witness=witness, work=meter.work,
            core_builds=built, row_updates=updates, assignments=assignments,
            point_queries=queries, bound_rejections=rejected, feasible_assignments=feasible,
            total_assignments=1 << len(plan.exceptions))

    def build():
        nonlocal built, updates, rows
        height, width = plan.maximum_q+1, plan.width
        meter.tick(height+2)
        rows = [0]*height
        rows[0] = 1 << -plan.r_min
        mask = (1 << width)-1
        histories.append((rows[0],))
        parent.peak_dp_bits = max(parent.peak_dp_bits, plan.dp_bits)
        parent.peak_history_bits = max(parent.peak_history_bits, plan.history_bits)
        prefix = 0
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

    try:
        if mode == "fast_eager":
            build()
        meter.tick(len(plan.core))
        core_total = sum(geometry.base*geometry.p[i]+geometry.r[i] for i in plan.core)
        exceptional_sum = previous_gray = 0
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
            low = max(0, (target-plan.r_max+geometry.base-1)//geometry.base)
            high = min(plan.maximum_q, (target-plan.r_min)//geometry.base)
            if target < 0 or target > core_total or low > high:
                rejected += 1
                continue
            feasible += 1
            if mode == "bounds_only":
                return finish("unresolved", "bounds_inconclusive")
            if rows is None:
                build()
            for q in range(low, high+1):
                meter.tick()
                queries += 1
                residual = target-geometry.base*q
                bit = residual-plan.r_min
                if not (0 <= bit < plan.width and rows[q] >> bit & 1):
                    continue
                meter.tick(3*len(geometry.p)+4)
                chosen = [i for j, i in enumerate(plan.exceptions) if gray >> j & 1]
                remaining_q, remaining_r = q, residual
                for position in range(len(plan.core)-1, -1, -1):
                    old = histories[position]
                    bit = remaining_r-plan.r_min
                    if (0 <= remaining_q < len(old) and 0 <= bit < plan.width
                            and old[remaining_q] >> bit & 1):
                        continue
                    index = plan.core[position]
                    chosen.append(index)
                    remaining_q -= geometry.p[index]
                    remaining_r -= geometry.r[index]
                if remaining_q or remaining_r:
                    raise AssertionError("bounds-core reconstruction failed")
                return finish("yes", "exception_core_witness", tuple(sorted(chosen)))
        return finish("no", "exception_bounds_exhausted" if not built else "exception_assignments_exhausted")
    except CheckLimit:
        return finish("unresolved", "exception_core_work_limit")
