"""Build Note VII evidence tables and figures from frozen studies 04 and 05."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from Structural_Geometry_Subset_Sum.exception_study import verify as verify04
from Structural_Geometry_Subset_Sum.bounds_study import verify as verify05
from Structural_Geometry_Subset_Sum.study import check_manifest, read_jsonl

OUTPUT = ROOT/'notes/07-geometric-cores'
BASE = ROOT/'Structural_Geometry_Subset_Sum/results'
STUDIES = {'04':BASE/'04_exception_core_20261028','05':BASE/'05_bounds_first_20261028'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    summaries,inputs = {},{}
    for key,folder in STUDIES.items():
        (verify04 if key=='04' else verify05)(folder)
        for manifest in ('data_hashes.json','evaluation_hashes.json'):
            check_manifest(folder,manifest)
        validation = json.loads((folder/'VALIDATION.json').read_text())
        assert validation['status']=='passed'
        for name in ('protocol.json','protocol.sha256','VALIDATION.json','summary.json',
                'cases.jsonl','counter_runs.jsonl','data_hashes.json','evaluation_hashes.json'):
            inputs[str((folder/name).relative_to(ROOT))] = sha(folder/name)
        summaries[key] = json.loads((folder/'summary.json').read_text())
        cases = read_jsonl(folder/'cases.jsonl')
        runs = read_jsonl(folder/'counter_runs.jsonl')
        assert len(cases)==summaries[key]['cases']
        assert len({c['list_id'] for c in cases})==summaries[key]['lists']
        policies = set(summaries[key]['work'])
        assert len(runs)==len(cases)*len(policies)
        assert len({(r['case_id'],r['policy']) for r in runs})==len(runs)
        counts = Counter(r['policy'] for r in runs if r['result']['status']!='unresolved')
        for policy in policies:
            assert counts[policy]==summaries[key]['work'][policy]['completed']
        for comparison in [summaries[key]['primary']]:
            assert comparison['difference']==comparison['first_only']-comparison['second_only']
    a,b = summaries['04'],summaries['05']
    assert a['primary']['difference']==a['work']['reuse']['completed']-a['work']['root']['completed']
    assert b['primary']['difference']==b['work']['bounds_first']['completed']-b['work']['reuse']['completed']
    for row in b['comparisons'].values():
        assert row['completions']['difference']==row['completions']['first_only']-row['completions']['second_only']
    events = [r['result']['core_event'] for r in read_jsonl(STUDIES['05']/'counter_runs.jsonl')
        if r['policy']=='bounds_first' and r['result']['core_event'] is not None]
    assert len(events)==b['work']['bounds_first']['core_calls']
    assert sum(e['core_builds'] for e in events)==b['work']['bounds_first']['core_builds']
    no_build = [e for e in events if e['reason']=='exception_bounds_exhausted']
    assert len(no_build)==b['work']['bounds_first']['bounds_no']
    assert all(e['core_builds']==0 and e['assignments']==e['total_assignments'] for e in no_build)
    return summaries,inputs


def main():
    data,inputs = verify()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    a,b = data['04'],data['05']
    def number(x): return f'{x:,}'
    def interval(row): return '['+', '.join(f'{v:.2f}' for v in row['list_bootstrap_95'])+']'
    saved = b['work']['reuse']['capped_cost']-b['work']['bounds_first']['capped_cost']
    avoided = b['work']['fast_eager']['core_builds']-b['work']['bounds_first']['core_builds']
    values = dict(SevenFirstCases=a['cases'],SevenFirstRoot=a['work']['root']['completed'],
        SevenFirstReuse=a['work']['reuse']['completed'],SevenFirstGain=a['primary']['difference'],
        SevenFirstInterval=interval(a['primary']),SevenSecondCases=b['cases'],
        SevenSecondRoot=b['work']['root']['completed'],SevenSecondReuse=b['work']['reuse']['completed'],
        SevenSecondBounds=b['work']['bounds_first']['completed'],SevenSecondOnly=b['work']['bounds_only']['completed'],
        SevenSecondGain=b['comparisons']['root']['completions']['difference'],
        SevenSecondInterval=interval(b['comparisons']['root']['completions']),
        SevenIncrement=b['primary']['difference'],SevenIncrementInterval=interval(b['primary']),
        SevenWorkSaved=saved,SevenWorkPercent=f'{100*saved/b["work"]["reuse"]["capped_cost"]:.2f}',
        SevenAvoided=avoided,SevenEagerBuilds=b['work']['fast_eager']['core_builds'],
        SevenLazyBuilds=b['work']['bounds_first']['core_builds'])
    (OUTPUT/'study_values.tex').write_text('% Generated from verified frozen studies; do not hand edit.\n'+
        '\n'.join('\\newcommand{\\'+k+'}{'+(number(v) if isinstance(v,int) else v)+'}' for k,v in values.items())+'\n',encoding='utf-8')
    labels = dict(lean='Lean, no geometry',root='Root geometry',discover_only='Discovery only',
        reuse='Exception-core reuse',direct_mitm='Direct MITM',bounds_only='Bounds only',
        bounds_first='Bounds first + reuse',fast_eager='Fast discovery, eager table')
    lines = [r'\begin{table}[htbp]',r'\centering\small',r'\begin{tabular}{@{}llrrl@{}}',
        r'\toprule',r'Study & Policy & Exact / targets & Capped work & Live 20ms [range] \\',r'\midrule']
    for key,s in data.items():
        if key=='05': lines.append(r'\midrule')
        for p,w in s['work'].items():
            t=s['live'][p]
            lines.append(f'{key} & {labels[p]} & {w["completed"]}/{s["cases"]} & {number(w["capped_cost"])} & {t["median"]} [{t["minimum"]},{t["maximum"]}] '+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\caption{Individual 32L work caps and separate live 20ms medians over three orders. Counts in different studies have different denominators. Capped work charges unresolved calls their full allowance. All acquisition, checking, fallback and verification are paid.}',r'\label{tab:results}',r'\end{table}']
    (OUTPUT/'results_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines = [r'\begin{table}[htbp]',r'\centering\small',r'\begin{tabular}{@{}lrrrr@{}}',r'\toprule',
        r'Policy & Core calls & Tables built & Point queries & Discovery work \\',r'\midrule']
    for p in ('reuse','bounds_only','fast_eager','bounds_first'):
        w=b['work'][p]
        lines.append(f'{labels[p]} & {w["core_calls"]} & {w["core_builds"]} & {w["point_queries"]} & {number(w["discovery_work"])} '+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\caption{Study 05 mechanism ablation. Fast-eager and bounds-first select the same plans. The 90 omitted tables correspond to complete bounds-only NO certificates.}',r'\label{tab:ablation}',r'\end{table}']
    (OUTPUT/'ablation_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
        'axes.spines.right':False,'axes.labelcolor':'#26231f','text.color':'#26231f','pdf.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(9,3.6),gridspec_kw={'width_ratios':[1.7,1]})
    rows=[a['primary'],b['comparisons']['root']['completions'],b['primary']]
    denominators=[a['cases'],b['cases'],b['cases']]
    vals=np.array([r['difference']/d*100 for r,d in zip(rows,denominators)])
    bounds=np.array([np.array(r['list_bootstrap_95'])/d*100 for r,d in zip(rows,denominators)])
    y=np.arange(3)[::-1]
    axes[0].errorbar(vals,y,xerr=np.vstack((vals-bounds[:,0],bounds[:,1]-vals)),
        fmt='o',color='#705840',capsize=4,linewidth=1.8)
    axes[0].axvline(0,color='#aaa29a',linewidth=.8)
    axes[0].set_yticks(y,['04: reuse − root\n(primary)','05: bounds first − root\n(secondary)',
        '05: bounds first − reuse\n(primary)'])
    axes[0].set_xlabel('Exact-completion difference (percentage points)')
    axes[0].set_title('A. Completion gains and their limits',loc='left',fontweight='bold',pad=15)
    axes[0].set_ylim(-.5,2.5)
    bars=axes[1].bar(['Eager','Bounds first'],[b['work']['fast_eager']['core_builds'],b['work']['bounds_first']['core_builds']],
        color=['#a99c8e','#705840'],width=.6)
    axes[1].bar_label(bars,padding=4)
    axes[1].set_ylim(0,225)
    axes[1].set_ylabel('Core tables constructed')
    axes[1].set_title('B. Same plans, fewer tables',loc='left',fontweight='bold',pad=15)
    fig.tight_layout(w_pad=2.4)
    for suffix in ('pdf','png'):
        fig.savefig(OUTPUT/f'geometric_gain.{suffix}',dpi=190,bbox_inches='tight')
    plt.close(fig)
    outputs=['study_values.tex','results_table.tex','ablation_table.tex','geometric_gain.pdf','geometric_gain.png']
    evidence=dict(status='verified',generator_sha256=sha(Path(__file__)),input_sha256=inputs,
        studies={key:dict(cases=s['cases'],lists=s['lists'],primary=s['primary'],validation=json.loads((STUDIES[key]/'VALIDATION.json').read_text())) for key,s in data.items()},
        derived=dict(values=values,capped_work_saved=saved,tables_avoided=avoided),
        claim_boundaries='No experiment rerun, model fit, new timing trial or new bootstrap performed. Stored bootstrap endpoints are rescaled only for the figure. Secondary comparisons remain exploratory.',
        output_sha256={name:sha(OUTPUT/name) for name in outputs})
    (OUTPUT/'paper_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('Note VII artifacts generated from verified studies 04 and 05; no solver/model reruns.')


if __name__=='__main__':
    main()
