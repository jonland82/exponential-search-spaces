"""Training-only prototype geometry and fixed structural interactions.

These features describe budgeted portfolio completion, not reachability or
intrinsic hardness. No visualization coordinates or evaluation labels are used.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits


INTERACTIONS = tuple(combinations(range(5), 2))
ARMS = ("baseline", "prototypes", "interactions", "combined")


class PrototypeGeometry:
    def __init__(self, x, y, groups, *, prototypes=3, seed=740281026):
        self.raw = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=int)
        self.groups = np.asarray(groups)
        if (self.raw.ndim != 2 or self.raw.shape[1] != 15 or
                len(self.raw) != len(self.y) or len(self.y) != len(self.groups) or
                set(self.y) != {0, 1} or prototypes < 1 or
                not np.isfinite(self.raw).all()):
            raise ValueError("geometry needs finite 15-feature rows, groups and both labels")
        self.prototypes = prototypes
        self.seed = seed
        self.scaler = StandardScaler().fit(self.raw)
        self.z = self.scaler.transform(self.raw)
        self.centers = self.fit_centers()

    def fit_centers(self, exclude_group=None):
        """Each list has total weight one within each class it contributes to."""
        centers = []
        for label in (0, 1):
            keep = self.y == label
            if exclude_group is not None:
                keep &= self.groups != exclude_group
            rows = self.z[keep]
            groups = self.groups[keep]
            if not len(rows):
                raise ValueError("list exclusion leaves an empty prototype class")
            _, inverse, counts = np.unique(groups, return_inverse=True, return_counts=True)
            weights = 1.0 / counts[inverse]
            k = min(self.prototypes, len(np.unique(rows, axis=0)))
            # Bound offline parallelism and make repeated audit fits reproducible.
            with threadpool_limits(limits=1):
                model = KMeans(n_clusters=k, random_state=self.seed, n_init=10,
                               max_iter=300, algorithm="lloyd").fit(rows, sample_weight=weights)
            centers.append(model.cluster_centers_)
        return centers

    def class_distances(self, x, exclude_groups=None):
        z = self.scaler.transform(np.asarray(x, dtype=float))
        return self._class_distances(z, exclude_groups)

    def _class_distances(self, z, exclude_groups=None):
        if exclude_groups is None:
            return np.column_stack([
                np.linalg.norm(z[:, None, :] - c[None, :, :], axis=2).min(axis=1)
                for c in self.centers])
        if len(exclude_groups) != len(z):
            raise ValueError("one excluded list is required per training row")
        result = np.empty((len(z), 2))
        for group in np.unique(exclude_groups):
            mask = np.asarray(exclude_groups) == group
            centers = self.fit_centers(group)
            for label, c in enumerate(centers):
                result[mask, label] = np.linalg.norm(
                    z[mask, None, :] - c[None, :, :], axis=2).min(axis=1)
        return result

    def interaction_values(self, x):
        z = self.scaler.transform(np.asarray(x, dtype=float))
        return self._interaction_values(z)

    @staticmethod
    def _interaction_values(z):
        return np.column_stack([z[:, i] * z[:, j] for i, j in INTERACTIONS])

    def work(self, arm):
        """Additional per-row heterogeneous work beyond the common classifier.

        45 standardization operations; 46 per 15D prototype distance plus
        minima; ten scalar products if requested. KMeans is entirely offline.
        This is a declared scale, not a uniform CPU/bit-operation count.
        """
        if arm not in ARMS:
            raise ValueError(arm)
        if arm == "baseline":
            return 0
        centers = sum(map(len, self.centers))
        return 45 + (centers * 47 if arm in ("prototypes", "combined") else 0) + (
            len(INTERACTIONS) if arm in ("interactions", "combined") else 0)


def design(x, geometry, arm, *, distances=None, exclude_groups=None):
    x = np.asarray(x, dtype=float)
    if arm not in ARMS:
        raise ValueError(arm)
    parts = [x]
    z = geometry.scaler.transform(x) if arm != "baseline" else None
    if arm in ("prototypes", "combined"):
        parts.append(geometry._class_distances(z, exclude_groups) if distances is None else distances)
    if arm in ("interactions", "combined"):
        parts.append(geometry._interaction_values(z))
    return np.column_stack(parts)


class GeometricModel:
    """Adapter charges geometry inside the existing live inference call."""
    def __init__(self, geometry, arm, fitted):
        self.geometry, self.arm, self.fitted = geometry, arm, fitted

    def predict_proba(self, x):
        return self.fitted.predict_proba(design(x, self.geometry, self.arm))
