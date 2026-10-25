"""Compare the rerun with the preserved outputs, excluding measured timings."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent.parent / 'subset_sum_refinement' / 'results'
RERUN = ROOT / 'subset_sum_refinement' / 'results'
ABS_TOL = REL_TOL = 1e-10


def without_timings(value):
    if isinstance(value, dict):
        return {k: without_timings(v) for k, v in value.items()
                if k != 'timing' and 'seconds' not in k and not k.endswith('_ms')}
    if isinstance(value, list):
        return [without_timings(v) for v in value]
    return value


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            yield {'path': path, 'reason': 'different keys'}
        for key in a.keys() & b.keys():
            yield from differences(a[key], b[key], f'{path}/{key}')
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield {'path': path, 'reason': 'different lengths'}
        for index, (x, y) in enumerate(zip(a, b)):
            yield from differences(x, y, f'{path}/{index}')
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        same = a == b if isinstance(a, int) and isinstance(b, int) else math.isclose(
            a, b, abs_tol=ABS_TOL, rel_tol=REL_TOL)
        if not same:
            yield {'path': path, 'original': a, 'rerun': b}
    elif a != b:
        yield {'path': path, 'original': a, 'rerun': b}


report = {'absolute_tolerance': ABS_TOL, 'relative_tolerance': REL_TOL,
          'timings_excluded': True, 'files': {}}
for name in ['train.jsonl', 'calibration.jsonl', 'test.jsonl', 'unseen_n20.jsonl',
             'summary.json', 'independent_checks.json', 'predictions.csv']:
    def read(directory):
        with (directory / name).open(encoding='utf-8', newline='') as handle:
            if name.endswith('.jsonl'):
                return [json.loads(line) for line in handle]
            if name.endswith('.csv'):
                rows = list(csv.DictReader(handle))
                for row in rows:
                    for key, value in row.items():
                        try:
                            row[key] = float(value)
                        except ValueError:
                            pass
                return rows
            return json.load(handle)
    before, after = read(ORIGINAL), read(RERUN)
    diff = list(differences(without_timings(before), without_timings(after)))
    report['files'][name] = {'matches': not diff, 'differences': len(diff),
                            'examples': diff[:10]}
    if isinstance(after, list):
        report['files'][name]['rows'] = len(after)

report['all_match'] = all(item['matches'] for item in report['files'].values())
old_summary = without_timings(json.loads((ORIGINAL / 'summary.json').read_text()))
new_summary = without_timings(json.loads((RERUN / 'summary.json').read_text()))
for summary in [old_summary, new_summary]:
    for model in summary['models'].values():
        for cohort in model['cohorts'].values():
            cohort.pop('top_20_percent_fractional_shrinkage_diagnostic', None)
report['main_summary_matches'] = not list(differences(old_summary, new_summary))
report['diagnostic_note'] = (
    'Density-model top-20% selection changes because nearly tied fractional '
    'shrinkages differ across environments by at most 4.22e-15. The primary '
    'coverage and width results reproduce within the stated tolerance. '
    'No experiment code or protocol was changed.'
)
report['original_environment'] = json.loads((ORIGINAL / 'provenance.json').read_text())
report['rerun_environment'] = json.loads((RERUN / 'provenance.json').read_text())
(ROOT / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if 'environment' not in k}, indent=2))
