"""Training-only recursive elimination and dependency-aware selected features."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from geometric_models import INTERACTIONS


LOGISTIC = dict(C=1., max_iter=2000, random_state=630251026)
ARMS = ("baseline", "combined", "top10", "top5")


def select_features(x, y):
    """Fixed-C, one-at-a-time RFE on standardized training features only.

    Drop smallest abs(coef); exact ties drop the lowest original column index.
    Final survivors are ordered by decreasing final abs(coef), then index.
    Rankings are conditional on this model and its correlated candidates.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=int)
    if x.ndim != 2 or x.shape[1] != 27 or set(y) != {0, 1} or not np.isfinite(x).all():
        raise ValueError("selection requires 27 finite candidate inputs and both labels")
    active, removed, trace, selected = list(range(27)), [], [], {}
    with threadpool_limits(limits=1):
        while True:
            fitted = make_pipeline(StandardScaler(), LogisticRegression(**LOGISTIC)).fit(x[:, active], y)
            coefficients = fitted[-1].coef_[0]
            if len(active) in (10, 5):
                selected[f"top{len(active)}"] = active.copy()
            drop = None if len(active) == 5 else min(
                range(len(active)), key=lambda j:(abs(coefficients[j]), active[j]))
            trace.append(dict(active=active.copy(), coefficients=coefficients.tolist(),
                intercept=float(fitted[-1].intercept_[0]),
                removed=None if drop is None else active[drop]))
            if drop is None:
                survivors = sorted(active, key=lambda i:(-abs(coefficients[active.index(i)]), i))
                break
            removed.append(active.pop(drop))
    return dict(selected=selected, ranking=survivors+list(reversed(removed)), trace=trace)


class PruningGeometry:
    """Frozen geometry with selected transformations and explicit dependencies."""
    def __init__(self, geometry, selected):
        self.geometry = geometry
        self.selected = {arm:list(columns) for arm, columns in selected.items()}
        for arm, columns in self.selected.items():
            if arm not in ("top5", "top10") or len(columns) != int(arm[3:]) or len(set(columns)) != len(columns) or any(not 0 <= i < 27 for i in columns):
                raise ValueError("invalid selected column set")

    def class_distances(self, x):
        return self.geometry.class_distances(x)

    def interaction_values(self, x):
        return self.geometry.interaction_values(x)

    def transform(self, x, arm):
        """Only compute selected derived columns, including their dependencies."""
        x = np.asarray(x, dtype=float)
        columns = self.selected[arm]
        derived = any(i >= 15 for i in columns)
        z = self.geometry.scaler.transform(x) if derived else None
        cache = {}
        for i in columns:
            if i < 15:
                cache[i] = x[:, i]
            elif i < 17:
                centers = self.geometry.centers[i-15]
                cache[i] = np.linalg.norm(z[:, None, :]-centers[None, :, :], axis=2).min(axis=1)
            else:
                a, b = INTERACTIONS[i-17]
                cache[i] = z[:, a]*z[:, b]
        return np.column_stack([cache[i] for i in columns])

    def dependencies(self, arm):
        columns = self.selected[arm]
        raw = {i for i in columns if i < 15}
        for i in columns:
            if 15 <= i < 17:
                raw.update(range(15))
            elif i >= 17:
                raw.update(INTERACTIONS[i-17])
        return sorted(raw)

    def work(self, arm):
        if arm in ("baseline", "combined"):
            return self.geometry.work(arm)
        columns = self.selected[arm]
        if not any(i >= 15 for i in columns):
            return 0
        centers = sum(len(self.geometry.centers[i-15]) for i in columns if 15 <= i < 17)
        products = sum(i >= 17 for i in columns)
        return 45 + 47*centers + products


class PrunedModel:
    def __init__(self, bank, arm, fitted):
        self.bank, self.arm, self.fitted = bank, arm, fitted

    def predict_proba(self, x):
        return self.fitted.predict_proba(self.bank.transform(x, self.arm))
