"""Independent saved-record audit for the frozen prediction/priority study."""

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import sys

import joblib
import numpy as np

from advanced_features import reduce_instance
from fit_development import metrics
from priority_experiment import aggregate, replay_pool
from prospective_study import (ARMS, CONFIG, cohort_for, encode_signature,
                                feature_vectors, infer, read_jsonl, verify)
from run_pilot import check, sha


def canonical(value):
    return json.loads(json.dumps(value))


def hashes(output, manifest):
    for name, digest in json.loads((output / manifest).read_text()).items():
        if sha(output / name) != digest:
            raise AssertionError(f"artifact hash mismatch: {name}")


def validate(output):
    protocol = verify(output)
    started = json.loads((output / "generation.started.json").read_text())["utc"]
    if datetime.fromisoformat(started) <= datetime.fromisoformat(protocol["frozen_at_utc"]):
        raise AssertionError("generation did not follow the freeze")
    for manifest in ("data_hashes.json", "prediction_hashes.json", "priority_hashes.json"):
        hashes(output, manifest)
    lists = read_jsonl(output / "lists.jsonl")
    cases = read_jsonl(output / "cases.jsonl")
    references = read_jsonl(output / "references.jsonl")
    by_case = {c["case_id"]: c for c in cases}
    by_list = {r["list_id"]: r for r in lists}
    if len(by_case) != len(cases) or len(by_list) != len(lists):
        raise AssertionError("duplicate case/list IDs")
    signatures = [encode_signature(row["weights"]) for row in lists]
    if len(set(signatures)) != len(signatures) or set(signatures) & set(protocol["prior_signatures"]):
        raise AssertionError("fresh-list overlap")
    pairs = {}
    for row in lists:
        if row["cohort"] != cohort_for(row["n"], row["family"], row["scale"]):
            raise AssertionError("cohort mismatch")
        original = tuple(w // row["scale"] for w in row["weights"])
        if any(w % row["scale"] for w in row["weights"]):
            raise AssertionError("scaling mismatch")
        if pairs.setdefault(row["base_list_id"], original) != original:
            raise AssertionError("scaled lists do not share the same base")
    scaled_vectors = {}
    for case in cases:
        row = by_list[case["list_id"]]
        if case["weights"] != row["weights"] or case["cohort"] != row["cohort"]:
            raise AssertionError("case metadata mismatch")
        kernel = reduce_instance(case["weights"], case["target"])
        expected, recorded = asdict(kernel), dict(case["kernel"])
        expected.pop("seconds")
        recorded.pop("seconds")
        if canonical(expected) != recorded:
            raise AssertionError("target reduction mismatch")
        vectors, work, _, reuse = feature_vectors(case["weights"], case["target"], kernel)
        if vectors != case["vectors"] or work != case["feature_work"] or canonical(reuse) != case["reuse"]:
            raise AssertionError("feature/certificate reuse mismatch")
        if len(vectors["five"]) != 5 or len(vectors["conventional"]) != 10 or len(vectors["hybrid"]) != 15:
            raise AssertionError("model dimension mismatch")
        pair = (case["base_list_id"], case["target_rule"])
        pair_value = (case["target"] // case["scale"], case["oracle_mask"], vectors["five"])
        if scaled_vectors.setdefault(pair, pair_value) != pair_value:
            raise AssertionError("paired targets/answers/structural distances changed under scaling")
        mask = case["oracle_mask"]
        if (mask is not None) != (case["truth"] == "yes"):
            raise AssertionError("oracle truth mismatch")
        if mask is not None and (mask < 0 or mask >> len(case["weights"]) or
                sum(w for i, w in enumerate(case["weights"]) if mask >> i & 1) != case["target"]):
            raise AssertionError("invalid oracle witness")
        check(case["weights"], case["target"], case["truth"] == "yes", reuse)
    indexed_refs = {}
    for ref in references:
        case = by_case[ref["case_id"]]
        key = (ref["case_id"], ref["mode"], ref["repeat"])
        if key in indexed_refs:
            raise AssertionError("duplicate reference record")
        indexed_refs[key] = ref
        check(case["weights"], case["target"], case["truth"] == "yes", ref)
        if ref["work"] != case["kernel"]["work"] + sum(a["work"] for a in ref["attempts"]):
            raise AssertionError("reference work mismatch")
        if ref["work"] > case["budget"]:
            raise AssertionError("reference work budget overrun")
    if len(references) != len(cases) * (CONFIG["timing_repeats"] + 1):
        raise AssertionError("missing reference records")
    bundles = joblib.load(output / "models.joblib")
    saved = json.loads((output / "prediction_metrics.json").read_text())
    y = np.array([int(indexed_refs[(c["case_id"], "work", 0)]["status"] != "unresolved") for c in cases])
    for arm in ARMS:
        for kind in ("logistic", "forest"):
            name = f"{arm}:{kind}"
            probabilities, work, _ = infer(bundles[name], [c["vectors"][arm] for c in cases])
            np.testing.assert_allclose(probabilities, [c["predictions"][name] for c in cases], rtol=0, atol=1e-12)
            if work != [c["inference_work"][name] for c in cases]:
                raise AssertionError("inference work mismatch")
            for cohort in saved["models"][name]:
                indices = [i for i, c in enumerate(cases) if c["cohort"] == cohort]
                score = metrics(y[indices], [cases[i]["predictions"][name] for i in indices])
                if score != saved["models"][name][cohort]["all"]:
                    raise AssertionError("prediction metric mismatch")
    pools = {}
    for c in cases:
        pools.setdefault(c["cohort"], []).append(c)
    runs = read_jsonl(output / "priority_runs.jsonl")
    work_map = {c["case_id"]: indexed_refs[(c["case_id"], "work", 0)] for c in cases}
    unique = set()
    for row in runs:
        key = (row["mode"], row["cohort"], row["fraction"], row["repeat"], row["policy"])
        if key in unique:
            raise AssertionError("duplicate pool run")
        unique.add(key)
        if len(set(row["solved_ids"])) != row["solved"]:
            raise AssertionError("duplicate counted completion")
        if any(by_case[i]["cohort"] != row["cohort"] for i in row["solved_ids"]):
            raise AssertionError("completion in wrong pool")
        if row["mode"] == "work":
            if row["spent"] > row["budget"] or sum(row["costs"].values()) != row["spent"]:
                raise AssertionError("work-pool charge mismatch")
            replay = replay_pool(pools[row["cohort"]], work_map, row["policy"], row["fraction"], row["repeat"])
            if replay != row:
                raise AssertionError("counter replay differs from saved policy trace")
        else:
            if sum(row["costs"].values()) > row["spent"] + 1e-6:
                raise AssertionError("time phase costs exceed elapsed interval")
            if abs(row["overshoot_seconds"] - max(0, row["spent"] - row["budget"])) > 1e-12:
                raise AssertionError("incorrect deadline overshoot")
            attempt_map = {a["case_id"]: a for a in row["attempts"]}
            for attempt in row["attempts"]:
                case = by_case[attempt["case_id"]]
                check(case["weights"], case["target"], case["truth"] == "yes",
                      {"status": attempt["returned_status"], "witness": attempt["witness"]})
                if attempt["within_case_deadline"] != (attempt["seconds"] <= attempt["allowance_seconds"]):
                    raise AssertionError("incorrect per-case deadline flag")
            for case_id in row["solved_ids"]:
                case = by_case[case_id]
                if case["kernel"]["status"] != "unresolved":
                    continue
                if row["policy"] in ("five", "hybrid", "distance_rule") and case["reuse"]["status"] != "unresolved":
                    continue
                if case_id not in attempt_map or attempt_map[case_id]["status"] == "unresolved":
                    raise AssertionError("counted an unresolved/late case")
    expected = len(pools) * 2 * CONFIG["pool_repeats"] * len(CONFIG["pool_policies"]) * 2
    if len(runs) != expected:
        raise AssertionError("missing pool runs")
    if aggregate(runs) != json.loads((output / "priority_summary.json").read_text()):
        raise AssertionError("priority summary mismatch")
    print(f"Validated frozen hashes/models, {len(pairs)} base lists / {len(lists)} encodings, "
          f"{len(cases)} cases, {len(references)} reference runs, all probabilities/metrics, "
          f"and {len(runs)} work/live policy runs. NO truths remain independent oracle records; "
          "this audit does not rerun exponential half enumeration.")


if __name__ == "__main__":
    validate(Path(sys.argv[1]))
