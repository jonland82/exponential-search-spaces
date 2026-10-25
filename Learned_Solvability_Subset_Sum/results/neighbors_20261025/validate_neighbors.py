"""Independent geometry/group/calibration audit plus full frozen-record replay."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from fit_development import matrix, read_jsonl
from neighbor_experiment import (CONFIG, DEVELOPMENT, ROOT, calibrated_bundle,
    probabilities, validate, verify)
from run_pilot import save_json, sha


def audit(output):
    protocol=verify(output)
    models=joblib.load(output/'models.joblib')
    bank=models['bank']
    development=read_jsonl(DEVELOPMENT/'cases.jsonl')
    common={r['case_id']:r for r in read_jsonl(DEVELOPMENT/'runs.jsonl') if r['policy']=='common'}
    train=[c for c in development if c['split']=='train']
    calibration=[c for c in development if c['split']=='calibration']
    x=matrix(train,'hybrid')
    y=np.array([int(common[c['case_id']]['status']!='unresolved') for c in train])
    groups=np.array([c['list_id'] for c in train])
    assert np.array_equal(groups,bank.groups)
    assert np.array_equal(y,bank.y)
    assert not set(groups)&{c['list_id'] for c in calibration}
    np.testing.assert_allclose(bank.scaler.mean_,x.mean(axis=0),rtol=0,atol=1e-12)
    scale=x.std(axis=0)
    scale[scale==0]=1
    np.testing.assert_allclose(bank.scaler.scale_,scale,rtol=0,atol=1e-12)
    z=(x-x.mean(axis=0))/scale
    np.testing.assert_allclose(bank.x,z,rtol=0,atol=1e-12)

    def brute_distances(query,exclusions=None):
        out=[]
        for i,row in enumerate(query):
            euclidean=np.linalg.norm((row-bank.scaler.mean_)/bank.scaler.scale_-bank.x,axis=1)
            values=[]
            for label in (0,1):
                candidates=[]
                for group in sorted(set(groups)):
                    if exclusions is not None and group==exclusions[i]:
                        continue
                    indices=np.flatnonzero((groups==group)&(y==label))
                    if len(indices):
                        candidates.append(min(euclidean[indices]))
                values.append(sum(sorted(candidates)[:5])/5)
            out.append(values)
        return np.array(out)

    training_distances=brute_distances(x,groups)
    saved=read_jsonl(output/'training_distances.jsonl')
    assert [r['case_id'] for r in saved]==[c['case_id'] for c in train]
    np.testing.assert_allclose(training_distances,[[r['hard_distance'],r['easy_distance']] for r in saved],rtol=0,atol=1e-12)
    cx=matrix(calibration,'hybrid')
    cy=np.array([int(common[c['case_id']]['status']!='unresolved') for c in calibration])
    cd=brute_distances(cx)
    for arm in ('hard','both','distances'):
        features=(np.column_stack((x,training_distances[:,0])) if arm=='hard' else
                  np.column_stack((x,training_distances)) if arm=='both' else training_distances)
        fit=make_pipeline(StandardScaler(),LogisticRegression(**CONFIG['logistic'])).fit(features,y)
        # Coefficients independently reproduce using brute-force list exclusions.
        actual=models['bundles'][arm]['model'].fitted
        np.testing.assert_allclose(fit.steps[1][1].coef_,actual.steps[1][1].coef_,rtol=0,atol=1e-10)
        cfeatures=(np.column_stack((cx,cd[:,0])) if arm=='hard' else np.column_stack((cx,cd)) if arm=='both' else cd)
        raw=np.clip(fit.predict_proba(cfeatures)[:,1],1e-6,1-1e-6)
        calibrator=LogisticRegression(**CONFIG['logistic']).fit(np.log(raw/(1-raw)).reshape(-1,1),cy)
        np.testing.assert_allclose(calibrator.coef_,models['bundles'][arm]['calibrator'].coef_,rtol=0,atol=1e-10)

    cases=read_jsonl(output/'cases.jsonl')
    predictions=read_jsonl(output/'predictions.jsonl')
    assert [r['case_id'] for r in predictions]==[c['case_id'] for c in cases]
    fresh_distances=brute_distances(np.array([c['vectors']['hybrid'] for c in cases]))
    np.testing.assert_allclose(fresh_distances,[[r['hard_distance'],r['easy_distance']] for r in predictions],rtol=0,atol=1e-12)
    pairs={}
    for c in cases:
        value=(tuple(w//c['scale'] for w in c['weights']),c['target']//c['scale'],c['truth'],c['oracle_mask'])
        assert not any(w%c['scale'] for w in c['weights'])
        assert c['target']%c['scale']==0
        assert pairs.setdefault((c['base_list_id'],c['target_rule']),value)==value
    # Verify confusion counts and accuracy without calling experiment metrics.
    fresh=json.loads((output/'prediction_metrics.json').read_text())['fresh']
    unscaled=[(c,r) for c,r in zip(cases,predictions) if c['scale']==1]
    for arm in CONFIG['arms']:
        confusion=[[0,0],[0,0]]
        for c,r in unscaled:
            truth=1-r['label']
            predicted=int(r['probabilities'][arm]<.5)
            confusion[truth][predicted]+=1
        recorded=fresh['models']['unscaled'][arm]['all']
        assert confusion==recorded['confusion_easy_hard']
        assert (confusion[0][0]+confusion[1][1])/576==recorded['accuracy_at_half']
    print('Independent audit passed: bank isolation, all distances, refits/calibration, scale pairing and confusion counts.',flush=True)
    validate(output)
    result=json.loads((output/'VALIDATION.json').read_text())
    result.update(independent_geometry_audit=True,training_refits_reproduced=True,calibration_reproduced=True,scale_pairs_checked=576)
    save_json(output/'INDEPENDENT_VALIDATION.json',result)
    shutil.copy2(Path(__file__),output/'validate_neighbors.py')
    # Final manifest includes every saved record and snapshot; it excludes itself.
    save_json(output/'artifact_hashes.json',{str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='artifact_hashes.json'})


if __name__=='__main__':
    audit(Path(sys.argv[1]))
