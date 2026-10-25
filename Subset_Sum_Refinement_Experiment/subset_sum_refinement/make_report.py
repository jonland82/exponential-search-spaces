"""Render the completed frozen experiment; no fitting or recalibration."""
import base64
import csv
import html
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
s = json.loads((OUT / 'summary.json').read_text())
names = ['learned', 'density', 'midpoint']
labels = ['Structural model', 'Simple density model', 'Calibrated midpoint']
colors = ['#2166ac', '#16806a', '#8796a5']
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout='constrained', dpi=170)
for ax, cohort, title in zip(axes, ['test', 'unseen_n20'],
                              ['Matched test: 1,000 fresh 16-item lists', 'Size transfer: 240 fresh 20-item lists']):
    x = np.arange(3)
    d = [s['models'][n]['cohorts'][cohort] for n in names]
    heights = [100*v['coverage'] for v in d]
    ci = np.array([v['coverage_binomial_95_ci'] for v in d]) * 100
    ax.scatter(x, heights, c=colors, s=90, zorder=3)
    ax.errorbar(x, heights, yerr=[np.array(heights)-ci[:, 0], ci[:, 1]-np.array(heights)],
                fmt='none', color='#172737', capsize=4, lw=1.3)
    ax.axhline(95, linestyle='--', color='#b34035', lw=1.4, label='95% target')
    for i, v in enumerate(d):
        ax.text(i, 77.0, f"{v['coverage']:.1%} covered\n{v['mean_fractional_shrinkage']:.1%} narrower",
                ha='center', va='center', fontsize=8.5, color='#172737', fontweight='bold')
    ax.set(ylim=(75, 102), xlim=(-.6, 2.6), xticks=x, xticklabels=['Structural\nmodel', 'Density\nmodel', 'Calibrated\nmidpoint'],
           ylabel='Exact fractions inside refined interval (%)', title=title)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.15)
    ax.set_axisbelow(True)
axes[0].legend(loc='upper left', fontsize=9)
fig.suptitle('Learned refinement works in distribution; size transfer can fail', fontsize=14, fontweight='bold')
fig.savefig(OUT / 'coverage.png')
plt.close(fig)

def pct(v):
    return f'{100*v:.1f}%'

def table(cohort):
    rows = []
    for name, label in zip(names, labels):
        d = s['models'][name]['cohorts'][cohort]
        ci = d['coverage_binomial_95_ci']
        rows.append(f"<tr><td>{label}</td><td>{d['covered']}/{d['lists']} ({pct(d['coverage'])})</td>"
                    f"<td>{pct(ci[0])}–{pct(ci[1])}</td><td>{pct(d['mean_fractional_shrinkage'])}</td>"
                    f"<td>{100*d['mean_new_width']:.2f} pp</td></tr>")
    return ('<div class="scroll"><table><thead><tr><th>Center</th><th>Observed coverage</th>'
            '<th>95% coverage CI</th><th>Mean width removed</th><th>Mean new width</th></tr></thead>'
            '<tbody>' + ''.join(rows) + '</tbody></table></div>')

primary = s['models']['learned']
test = primary['cohorts']['test']
ood = primary['cohorts']['unseen_n20']
timing = s['timing']
test_ms = 1000*(timing['test']['total_outer_seconds'] + timing['test']['total_feature_seconds'] + test['batched_prediction_seconds'])/1000
offline = sum(timing[x]['total_exact_label_seconds'] for x in ['train', 'calibration'])
image = base64.b64encode((OUT / 'coverage.png').read_bytes()).decode()
source = 'https://github.com/jonland82/semantic-boolean-complexity/blob/master/papers/learned-semantic-envelopes/learned-semantic-envelopes.tex'
failure = 'https://github.com/jonland82/semantic-boolean-complexity/blob/master/papers/selection-breaks-calibration/selection-breaks-calibration.tex'
body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Testing calibrated refinement for probability-valued subset sum</title>
<style>body{{font:17px/1.58 system-ui,sans-serif;color:#172737;background:#fff;margin:0 auto;max-width:1050px;padding:30px 22px 60px}}h1{{font-size:34px;line-height:1.18;margin-bottom:12px}}h2{{font-size:23px;margin-top:34px}}p{{max-width:85ch}}.lead{{font-size:21px}}.box{{background:#f0f5fa;border-left:4px solid #2166ac;padding:14px 20px}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:15px}}td,th{{padding:10px 12px;border-bottom:1px solid #d9e1e9;text-align:left}}th{{background:#f0f5fa}}img{{width:100%;height:auto}}code,pre{{font:14px/1.5 ui-monospace,monospace}}pre{{padding:14px;background:#f2f4f6;overflow:auto}}.small{{font-size:14px;color:#4b5966}}a{{color:#175d98}}@media(max-width:600px){{h1{{font-size:28px}}body{{padding:20px 16px}}}}</style></head><body>
<p class="small">Frozen exploratory experiment · October 22, 2026 · New independent lists</p>
<h1>Testing your bound-tightening method on Note III</h1>
<p class="lead"><strong>It worked on matched synthetic data.</strong> The main model removed {pct(test['mean_fractional_shrinkage'])} of the original interval width and covered {test['covered']} of {test['lists']} exact answers. But its coverage fell to {pct(ood['coverage'])} on larger lists without recalibration.</p>
<div class="box">The simple density baseline nearly matched the main model on the primary test and transferred better to larger lists. This supports calibrated refinement on this generator, with modest additional benefit from the richer structural model. It does not establish deterministic bounds for individual new lists.</div>
<h2>What was frozen before the test</h2>
<p>Using the repository’s weight generator and Note III’s target rule, generate 1,200 training lists, 500 calibration lists, and 1,000 untouched test lists, all with 16 weights. Each list independently belongs to the independent-weight or repeated-pair family with equal probability. Generate another 240 lists with 20 weights as a prespecified size-transfer stress test. The same fixed random seed, 731029, controls generation. No hyperparameter search, model selection, recalibration, or rule changes followed inspection of test results.</p>
<p>Targets are uniform on the integer middle 40% of each list’s total weight, conditional on passing reachable-residue screens modulo 8, 10, 16, and 32. The denominator is counted exactly via a period-160 residue calculation. All attainable sums automatically pass those screens.</p>
<p>The original lower endpoint is the fraction of eligible targets witnessed by 512 sampled subsets. The upper endpoint is the smaller of 1 and the number of multiplicity-count patterns divided by eligible-target count. Exact reachable fractions were computed by set enumeration for labels and evaluation only; they were excluded from test features and interval construction.</p>
<p>The primary predictor is a fixed gradient-boosted regressor of normalized position inside the original interval. It uses inexpensive list features: density, multiplicity, weight moments, small-block collisions, residue coverage, and original endpoints. The density baseline uses degree-two ridge regression on only density proxy, unique-weight fraction, and the original upper endpoint. The midpoint baseline predicts normalized position 1/2. All three receive the same one-sided normalized calibration procedure.</p>
<h2>Primary result: 16 weights</h2>
{table('test')}
<p>The original mean width was {100*test['mean_original_width']:.2f} percentage points. The structural model reduced that to {100*test['mean_new_width']:.2f} points. “Mean width removed” averages each list’s fractional reduction; it is not the ratio of the two mean widths. Coverage confidence intervals are exact binomial intervals for the fresh test cohort.</p>
<p>For independent weights, structural-model coverage was 499/499 (100%). For repeated pairs it was 476/501 (95.0%). All 25 misses were in the repeated-pair family. Marginal calibration does not promise identical family-specific coverage. The largest endpoint violation was {100*test['max_violation']:.2f} percentage points.</p>
<h2>Prespecified size-transfer stress test: 20 weights</h2>
{table('unseen_n20')}
<p>The structural model missed 27 of 240 exact fractions: 24 independent-weight lists and three repeated-pair lists. Its 88.8% observed coverage, with 95% binomial interval 84.1%–92.5%, demonstrates a failure to maintain the 95% target under this size shift. The density baseline retained 98.8% observed coverage on this cohort, but this is empirical transfer evidence, not a guarantee under arbitrary shifts. No method was recalibrated using these 240 lists.</p>
<img alt="Observed coverage and mean interval shrinkage for the three prespecified models on matched and larger-list tests" src="data:image/png;base64,{image}">
<p class="small">Whiskers: exact 95% binomial confidence intervals for observed coverage. Narrowness and coverage are distinct: the width formula still holds when an interval misses.</p>
<h2>The theorem checked numerically</h2>
<p>Let ℓ ≤ q ≤ u, W = u − ℓ, and q̂ = ℓ + pW, with p in [0,1]. On 500 calibration lists, the two one-sided scores are (q̂ − q)₊/W and (q − q̂)₊/W. Collapsed intervals contribute zero scores. For total error α = 0.05, the correction in each tail is ordered score number ceil((500 + 1) × 0.975) = 489. Under exchangeability, a union bound gives at least 95% marginal coverage.</p>
<pre>I* = [max(ℓ, q̂ − c⁻W), min(u, q̂ + c⁺W)]
width(I*) / W = min(p, c⁻) + min(1 − p, c⁺)
fraction removed ≥ max(0, 1 − c⁻ − c⁺)</pre>
<p>The structural-model corrections were c⁻ = {primary['c_minus']:.6f} and c⁺ = {primary['c_plus']:.6f}. Thus every noncollapsed interval, including the shifted-size cases, removed at least {pct(primary['pointwise_minimum_fractional_shrinkage'])} of its original width. The exact width identity, nonexpansion, and minimum-shrinkage inequality were checked for all 3,720 model/cohort predictions. Statistical containment does not follow from narrowness alone.</p>
<h2>Selection diagnostic</h2>
<p>The prespecified diagnostic retained the top 20% by predicted fractional shrinkage, using no test labels for selection. Structural-model coverage there was 197/200 (98.5%) on matched lists and 43/48 (89.6%) on larger lists. This particular selection did not create an additional observed collapse. It does not establish coverage conditional on arbitrary score-based selection; that remains subject to the issue in your selection paper.</p>
<h2>Checks and cost</h2>
<p>All 2,940 original certified intervals contained their exact reachable fraction. No weight list was duplicated across any cohorts. Set-enumeration labels were checked against brute force on 30 small inputs, and 12 primary-test labels were independently checked using integer-bitset dynamic programming. Every check passed.</p>
<p>The run took {timing['total_experiment_seconds']:.1f} seconds. Exact labels for training and calibration took {offline:.2f} seconds in total; fitting the structural model took {timing['primary_fit_seconds']:.2f} seconds. On 1,000 primary-test lists, outer-bound construction, feature extraction, and batched structural inference averaged {test_ms:.2f} ms per list. Exact enumeration averaged {1000*timing['test']['total_exact_label_seconds']/1000:.2f} ms per primary-test list. These compare different outputs: a statistical interval and the exact fraction. They are small Python benchmarks, not a claim of superiority over optimized bitset algorithms or a new complexity bound. Training-label costs are additional.</p>
<h2>Verdict</h2>
<p><strong>The method is applicable and produced useful tightening here.</strong> Most of the benefit was also available to a simple density model. The richer model’s smaller matched-data intervals came with a clear size-transfer failure. A next prospective study should freeze a multi-size training and calibration population and compare cost to reach a specified interval width against direct exact computation and exact-label sampling.</p>
<h2>Reproduce and inspect</h2>
<pre>OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python run_refinement.py
python make_report.py</pre>
<p>The companion ZIP includes the frozen protocol, source snapshots, SHA-256 provenance, generator and evaluation code, all per-list exact labels and weights, all interval predictions, independent checks, summary JSON, and this report. Python, NumPy, SciPy, scikit-learn, and Matplotlib are required; exact version numbers appear in provenance.json. Repeating the script checks that the protocol is unchanged. It regenerates results deterministically apart from timings.</p>
<p>Sources: <a href="https://github.com/jonland82/exponential-search-spaces/blob/master/notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex">Note III</a> · <a href="{source}">Your general calibrated-refinement theorem</a> · <a href="{failure}">Your selection-calibration analysis</a>.</p>
</body></html>'''
(ROOT / 'Subset_Sum_Refinement_Report.html').write_text(body)
(ROOT / 'requirements.txt').write_text('numpy==2.3.5\nscipy==1.17.0\nscikit-learn==1.8.0\nmatplotlib\n')
(ROOT / 'README.md').write_text('''# Calibrated refinement test for Note III

Open Subset_Sum_Refinement_Report.html for the complete result.
Install requirements.txt, then run:

    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python run_refinement.py
    python make_report.py

protocol.json was frozen before generating any labels. The primary test used
1,000 independent 16-item lists; the 240 20-item lists are a prespecified
size-transfer diagnostic. Sources are snapshots obtained through GitHub from
jonland82/exponential-search-spaces. No remote repository was modified.
The results directory contains exact labels, full weight lists, model
predictions, independent label checks, and SHA-256 provenance.
''')
archive = ROOT / 'Subset_Sum_Refinement_Experiment.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=7) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and p != archive and '__pycache__' not in str(p) and p.suffix != '.log':
            z.write(p, arcname='subset_sum_refinement/' + str(p.relative_to(ROOT)))
print(json.dumps({'report': str(ROOT / 'Subset_Sum_Refinement_Report.html'),
                  'archive': str(archive), 'archive_bytes': archive.stat().st_size,
                  'primary_mean_amortized_interval_ms': test_ms}, indent=2))
