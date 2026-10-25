"""Create Note V's typeset values and table from verified saved measurements."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper_catalog import PAPERS, directory


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    study = ROOT / "Structural_Distance_Subset_Sum/results/prospective_20261024"
    data = json.loads((study / "summary.json").read_text())
    protocol = json.loads((study / "protocol.json").read_text())
    assert digest(study / "protocol.json") == (study / "protocol.sha256").read_text().strip()
    for name, expected in protocol["protected_hashes"].items():
        assert digest(study / "sources" / name) == expected
        assert digest(ROOT / "Structural_Distance_Subset_Sum" / name) == expected
    for stage, filename, key in (
        ("timing.json", "runs.jsonl", "runs_sha256"),
        ("memory_stage.json", "memory.jsonl", "memory_sha256"),
    ):
        record = json.loads((study / stage).read_text())
        assert digest(study / filename) == record[key]
    assert data["mismatches"] == 0 and data["cases"] == 180
    output = directory(next(paper for paper in PAPERS if paper["number"] == "V"))
    def grouped(value):
        return f"{value:,}".replace(",", "{,}")
    values = {
        "StudyLists": data["lists"], "StudyTargets": data["cases"],
        "StudyRuns": data["timing_runs"], "StudyCorrect": data["completed_timing_answers"],
        "StudyStopped": data["timing_runs"] - data["completed_timing_answers"],
        "StudyProfiles": data["memory_runs"],
        "StudyMemoryCorrect": data["completed_memory_answers"],
        "SupportImproved": data["supports"]["select_support"]["improved"],
    }
    text = "% Generated from the frozen study; do not edit measured values.\n"
    text += "\n".join(
        f"\\newcommand{{\\{key}}}{{{grouped(value)}}}" for key, value in values.items()
    ) + "\n"
    (output / "study_values.tex").write_text(text, encoding="utf-8")
    rows = [
        "% Generated from the saved paired per-case summaries.",
        r"\begin{tabular}{lrrr}", r"\toprule",
        r"Method & Completed & Wins / paired & Median ratio\\", r"\midrule",
        f"Simple greedy core & {data['methods']['core_distinct']['completed_cases']}/{data['cases']} & --- & 1.000\\\\",
    ]
    for name, label in (
        ("select_multiplicity", "Multiplicity-ranked core"),
        ("select_support", "Exact-support probes"),
    ):
        item = data["methods"][name]
        pair = item["paired"]["core_distinct"]
        rows.append(
            f"{label} & {item['completed_cases']}/{data['cases']} & "
            f"{pair['wins']}/{pair['matched']} & {pair['median_ratio']:.3f}\\\\"
        )
    rows += [r"\bottomrule", r"\end{tabular}"]
    (output / "study_table.tex").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("Verified frozen evidence and generated Note V values and table.")


if __name__ == "__main__":
    build()
