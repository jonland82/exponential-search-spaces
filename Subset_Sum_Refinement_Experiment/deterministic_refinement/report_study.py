"""Summarize frozen evidence; does not fit, tune, or change any method."""
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'results'
rows = [json.loads(line) for line in (OUT/'prospective.jsonl').read_text().splitlines()]
s = json.loads((OUT/'prospective_summary.json').read_text())
reg = json.loads((OUT/'regression_summary.json').read_text())
protocol = json.loads((ROOT/'protocol.json').read_text())['protocol']


def pct(value):
    return f'{100*value:.2f}%'


def ms(value):
    return f'{1000*value:.3f}'


def method_rows(group, name):
    if name.startswith('sampling_'):
        trials = int(name.split('_')[1])
        return [next(v for v in r['sampling'] if v['trials'] == trials) for r in group]
    return [r['methods'][name] for r in group]


def accuracy_results(group):
    results = {}
    for epsilon in protocol['tolerances']:
        values = {}
        for name in protocol['methods']+['sampling']:
            attained, ratios, exact_faster = [], [], 0
            for row in group:
                if name == 'sampling':
                    candidates = [v for v in row['sampling'] if not v['empty'] and v['width'] <= epsilon]
                    result = candidates[0] if candidates else None
                else:
                    value = row['methods'][name]
                    result = value if value['width'] <= epsilon else None
                if result is not None:
                    best_exact = min(v['total_seconds'] for v in row['oracles'].values() if v['status'] == 'ok')
                    attained.append(result['total_seconds'])
                    ratios.append(result['total_seconds']/best_exact)
                    exact_faster += result['total_seconds'] >= best_exact
            values[name] = {'attained': len(attained), 'lists': len(group),
                            'median_ms_when_attained': 1000*statistics.median(attained) if attained else None,
                            'median_cost_ratio_to_fastest_exact_on_same_lists': statistics.median(ratios) if ratios else None,
                            'observed_faster_than_best_exact': len(attained)-exact_faster}
        results[str(epsilon)] = values
    return results


analysis = {
    'accuracy_attainment': accuracy_results(rows),
    'accuracy_by_stratum': {f'n{n}_{family}': accuracy_results([r for r in rows if r['n'] == n and r['family'] == family])
                           for n in protocol['sizes'] for family in protocol['families']},
    'sampling_simultaneous_covered': sum(all(v['covered'] for v in r['sampling']) for r in rows),
    'sampling_simultaneous_by_stratum': {
        f'n{n}_{family}': {'covered': sum(all(v['covered'] for v in r['sampling']) for r in rows if r['n'] == n and r['family'] == family),
                         'lists': sum(r['n'] == n and r['family'] == family for r in rows)}
        for n in protocol['sizes'] for family in protocol['families']},
    'residue_cap_strict_improvements': sum(r['methods']['combined']['R'] < r['methods']['partial_32']['R'] for r in rows),
    'combined_strictly_better_than_range': sum(r['methods']['combined']['width'] < r['methods']['range']['width']-1e-15 for r in rows),
    'combined_mean_extra_width_removed': statistics.mean(r['methods']['range']['width']-r['methods']['combined']['width'] for r in rows),
    'oracles': {}, 'memory': {},
}
for name in ['exact_set', 'bitset']:
    valid = [r['oracles'][name] for r in rows if r['oracles'][name]['status'] == 'ok']
    analysis['oracles'][name] = {'completed': len(valid), 'skipped': len(rows)-len(valid),
                                'median_ms_completed': 1000*statistics.median(v['total_seconds'] for v in valid),
                                'mean_ms_completed': 1000*statistics.mean(v['total_seconds'] for v in valid)}
for name in protocol['methods']+['sampling', 'exact_set', 'bitset']:
    peaks = [r['memory'][name]['peak_traced_bytes'] for r in rows if 'memory' in r and r['memory'][name]['status'] == 'ok']
    analysis['memory'][name] = {'profiled': len(peaks), 'median_peak_bytes': statistics.median(peaks),
                               'max_peak_bytes': max(peaks)}
(OUT/'analysis.json').write_text(json.dumps(analysis, indent=2)+'\n', encoding='utf-8')

# A standalone scientific chart; exact bitset points use feasible lists only.
colors = dict(original='#777777', range='#0072b2', partial_32='#56b4e9',
              combined='#009e73', sampling_512='#d55e00', sampling_2048='#cc79a7',
              exact_set='#111111', bitset='#e69f00')
fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout='constrained')
for ax, n in zip(axes.flat, protocol['sizes']):
    group = [r for r in rows if r['n'] == n]
    for name, color in colors.items():
        if name in ('exact_set', 'bitset'):
            values = [r['oracles'][name] for r in group if r['oracles'][name]['status'] == 'ok']
            x, y, marker = statistics.median(v['total_seconds'] for v in values)*1000, 0, 'X'
        else:
            values = method_rows(group, name)
            x = statistics.median(v['total_seconds'] for v in values)*1000
            y, marker = statistics.mean(v['width'] for v in values), 'o'
        ax.scatter(x, y, color=color, marker=marker, s=75, label=name.replace('_', ' '))
    ax.set(xscale='log', xlabel='Median total time (ms, log scale)',
           ylabel='Mean interval width', title=f'{n} weights; 40 fresh lists', ylim=(-.02, 1.02))
    ax.grid(alpha=.2)
handles, labels = axes.flat[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='outside lower center', ncol=4, frameon=False)
fig.suptitle('Certified width versus total work; exact and sampling baselines', fontsize=14)
fig.savefig(OUT/'width_vs_cost.png', dpi=180)
fig.savefig(OUT/'width_vs_cost.pdf')
plt.close(fig)

lines = [
    '# Deterministic subset-sum refinement: evidence report', '',
    'Completed October 23, 2026. This study implements steps 1–3 of the handoff. Its verified theory and measurements are now incorporated into the expanded [Paper III](../../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html). Publication integration did not change the frozen algorithms or evidence.', '',
    '## What was established', '',
    f"- The original range-only result reproduced: **{reg['overall']['range']['strictly_narrower']}/1,000** improved intervals, **{pct(reg['overall']['range']['mean_fractional_shrinkage'])}** mean per-list narrowing, and **1,000/1,000** containment.",
    f"- A protocol and source hashes were frozen before generating **{len(rows)}** fresh lists: 20 per family at each of 12, 16, 20, and 22 weights. No sorted weight list overlaps any of the 2,940 original lists.",
    f"- Every tested deterministic method contained every fresh exact answer. Bitset labels independently agreed on **{s['bitset_exact_agreements']}/{len(rows)}** feasible cases; **{s['bitset_skipped']}** exceeded the predeclared 100-million-bit cap after GCD compression.",
    f"- Partial collisions plus the residue cap narrowed **{analysis['combined_strictly_better_than_range']}/{len(rows)}** intervals further than range counting. The mean additional absolute width removed was **{analysis['combined_mean_extra_width_removed']:.8f}**.",
    f"- Exact-decision sampling covered the truth simultaneously at all three reported budgets on **{analysis['sampling_simultaneous_covered']}/{len(rows)}** lists; its simultaneous nominal coverage is at least 95% per list.",
    '',
    'The deterministic claim is proved algebraically in [THEOREM.md](THEOREM.md). Fresh containment is an implementation check, not the source of its universal validity. No new complexity or novelty claim follows from these experiments.', '',
    '## Original cohort: reproduction and collision oracle', '',
    '| Method | Contained truth | Mean per-list width removed | Mean width | Median incremental time (ms) |',
    '|---|---:|---:|---:|---:|',
]
for name, v in reg['overall'].items():
    lines.append(f"| {name} | {v['covered']}/1000 | {pct(v['mean_fractional_shrinkage'])} | {v['mean_width']:.6f} | {v['median_total_ms']:.3f} |")
lines += ['',
    'The reproduced mean range width is 0.372926981391316, from 0.4044522237405377. Mean-width reduction is 7.79%; the 13.10% number averages the fractional reduction separately on each list. These are different statistics.', '',
    'Regression timings reuse saved witnessed counts and exclude their original construction. The full-collision row uses the **exact target histogram and exact maximum representation count** as an evaluation oracle. Its time excludes half-set construction. A full histogram already reveals exact support; this row is diagnostic, not a proposed approximation algorithm.', '',
    '## Fresh study: all preprocessing charged', '',
    '| Method | Contained truth | Mean per-list width removed | Mean width | Median total time (ms) | Mean total time (ms) |',
    '|---|---:|---:|---:|---:|---:|',
]
for name in protocol['methods']:
    v = s['overall'][name]
    lines.append(f"| {name} | {v['covered']}/{len(rows)} | {pct(v['mean_fractional_shrinkage'])} | {v['mean_width']:.6f} | {v['median_total_ms']:.3f} | {v['mean_total_ms']:.3f} |")
for trials, v in s['sampling'].items():
    lines.append(f"| sampling {trials} | {v['covered']}/{len(rows)} | — | {v['mean_width']:.6f} | {v['median_total_ms']:.3f} | — |")
for name, v in analysis['oracles'].items():
    lines.append(f"| {name} | {v['completed']}/{v['completed']} feasible | 100% | 0 | {v['median_ms_completed']:.3f} | {v['mean_ms_completed']:.3f} |")
lines += ['',
    'Fresh deterministic times include denominator/residue construction, 512 subset witnesses, half-set construction, sorting, and every certificate calculation. Each method runs from scratch in a reproducibly shuffled order. Sampling includes the original interval, halves, target draws, exact YES/NO decisions, and checkpoint bands. Exact methods run independently and include denominator construction. Bitset medians concern only feasible cases, so they are not an all-cohort comparison.', '',
    '![Width versus cost](results/width_vs_cost.png)', '',
    'Chart points show median total time and mean width at each size, pooling the two families; bitset points use its feasible subset. Per-instance accuracy comparisons below avoid that subset mismatch.', '',
    '## Fresh results by size and family', '',
    '| Stratum | Lists | Range: narrowing / median ms | Combined: narrowing / median ms | Combined coverage |',
    '|---|---:|---:|---:|---:|',
]
for stratum, methods in s['strata'].items():
    a, b = methods['range'], methods['combined']
    lines.append(f"| {stratum} | {a['lists']} | {pct(a['mean_fractional_shrinkage'])} / {a['median_total_ms']:.3f} | {pct(b['mean_fractional_shrinkage'])} / {b['median_total_ms']:.3f} | {b['covered']}/{b['lists']} |")
lines += ['', '## Work to reach a prescribed probability width', '',
    'Each tolerance is a **full interval width**, matching the handoff convention. Deterministic methods have certified containment. Sampling uses a union bound over its three fixed checkpoints, so choosing the first successful reported checkpoint preserves at least 95% coverage. Empty statistical intersections never count as accuracy attainment.', '',
    'The exact reference is the faster of standalone truncated set DP and feasible GCD-compressed bitset DP on the **same list**. Ratios above 1 mean that exact computation was faster. One timing per list supports a descriptive comparison, not a stable speedup claim.', '',
    '| Width ≤ | Method | Lists attaining width | Median ms among attained | Median cost / fastest exact | Attained and observed faster than exact |',
    '|---|---|---:|---:|---:|---:|',
]
for epsilon, methods in analysis['accuracy_attainment'].items():
    for name, v in methods.items():
        t = '—' if v['median_ms_when_attained'] is None else f"{v['median_ms_when_attained']:.3f}"
        ratio = '—' if v['median_cost_ratio_to_fastest_exact_on_same_lists'] is None else f"{v['median_cost_ratio_to_fastest_exact_on_same_lists']:.2f}"
        lines.append(f"| {epsilon} | {name} | {v['attained']}/{v['lists']} | {t} | {ratio} | {v['observed_faster_than_best_exact']} |")
lines += ['', '## Memory', '',
    'Memory was measured separately with `tracemalloc` on the first list of each of the eight size/family strata. These repeated profiling runs do not supply the headline timings. Peak bytes include Python allocations and big integers during preprocessing and computation; they exclude the interpreter baseline, allocator retention, and untraced native allocations. They are not process RSS.', '',
    '| Method | Profiled feasible lists | Median traced peak (KiB) | Maximum traced peak (KiB) |',
    '|---|---:|---:|---:|',
]
for name, v in analysis['memory'].items():
    lines.append(f"| {name} | {v['profiled']} | {v['median_peak_bytes']/1024:.1f} | {v['max_peak_bytes']/1024:.1f} |")
lines += ['', '## How to interpret the evidence', '',
    'Range counting supplies most of the inexpensive deterministic improvement observed here. The tested partial-collision selection and residue caps add much less narrowing than the full histogram oracle. This identifies a certificate-quality bottleneck; it does not show that all inexpensive collision strategies must fail.', '',
    'The accuracy-attainment table determines whether any observed runtime savings meet a useful tolerance. Cheap but wide intervals and much slower narrow statistical bands should not be presented as an algorithmic advance. Costs and widths vary substantially by list, family, and scale; small per-stratum samples limit distributional conclusions.', '',
    'The old 77% statistical refinement result remains separate: it has been reproduced, but failed size transfer. This continuation does not refit a predictor or silently reuse its calibration constants.', '',
    'The revision to Paper III documents the range/collision theorem, the modest measured improvement, and the cost limitations alongside the separate calibrated results and their transfer failure. A literature assessment remains necessary before making novelty claims. The series remains four notes. The protected theory note retains its historical statement that Paper III was unchanged at the experiment stage.', '',
    '## Reproduction and artifacts', '',
    'No third-party dependencies are needed for the algorithms or tests. Matplotlib is required only for this report and its standalone PNG/PDF chart.', '',
    '```powershell',
    'python -m unittest -v test_bounds',
    'python run_study.py regression',
    'python run_study.py freeze',
    'python run_study.py prospective',
    'python report_study.py',
    '```', '',
    'The prospective command intentionally refuses to overwrite existing evidence. To repeat the study, copy the source and frozen protocol into a new directory beside this one, retaining access to the same preserved upstream dataset; alternatively retain the directory layout in a separate checkout. The protocol hashes protect `bounds.py`, `run_study.py`, `test_bounds.py`, and `THEOREM.md`.', '',
    '- [Frozen protocol and hashes](protocol.json)',
    '- [Proof and assumptions](THEOREM.md)',
    '- [Original-cohort regression summary](results/regression_summary.json)',
    '- [Fresh-study summary](results/prospective_summary.json)',
    '- [Accuracy, sampling, and memory analysis](results/analysis.json)',
    '- [Fresh weights generated before labels](results/prospective_weights.jsonl)',
    '- [Full per-list prospective measurements](results/prospective.jsonl)',
    '- [Source and dataset provenance](results/prospective_provenance.json)',
    '- [Saved-evidence verification](results/verification.json)',
    '- [Publication methods and generated artifacts](../../subset-sum/PROBABILITY_REFINEMENT.md)',
    '- [Standalone chart PDF](results/width_vs_cost.pdf)',
    '- Test output: `validation.log`; progress output: `regression.log`, `prospective.log`.', '',
    f"The complete prospective run, including separate memory profiling, took {s['study_wall_seconds_including_memory_profiling']:.1f} seconds on {json.loads((OUT/'prospective_provenance.json').read_text())['platform']} with Python {json.loads((OUT/'prospective_provenance.json').read_text())['python']}.",
]
(ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(json.dumps({'report': str(ROOT/'REPORT.md'), 'analysis': analysis}, indent=2))
