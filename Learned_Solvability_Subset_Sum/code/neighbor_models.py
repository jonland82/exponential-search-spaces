"""Training-only, list-aware empirical proximity features (not certificates)."""
from __future__ import annotations

import numpy as np
from sklearn.preprocessing import StandardScaler


class ReferenceBank:
    def __init__(self, x, y, groups, k=5):
        self.k = k
        self.scaler = StandardScaler().fit(x)
        self.x = self.scaler.transform(x)
        self.y = np.asarray(y, dtype=int)
        self.groups = np.asarray(groups)
        self.unique_groups = np.unique(self.groups)
        self.indices = [np.flatnonzero(self.groups == group) for group in self.unique_groups]
        if set(self.y) != {0, 1} or k < 1:
            raise ValueError('bank needs both classes and positive k')

    def distances(self, x):
        z = self.scaler.transform(np.asarray(x, dtype=float))
        # Direct differences avoid catastrophic cancellation for nearly equal rows.
        return np.sqrt(np.square(z[:, None, :] - self.x[None, :, :]).sum(axis=2))

    def class_distances(self, x, exclude_groups=None):
        """Mean distance to k nearest distinct lists in each class: hard, easy.

        A list can supply examples of both labels. Within each class its nearest
        target contributes once. Training rows exclude their entire own list.
        """
        distances = self.distances(x)
        output = []
        for label in (0, 1):
            columns = []
            for group, indices in zip(self.unique_groups, self.indices):
                indices = indices[self.y[indices] == label]
                if not len(indices):
                    continue
                column = distances[:, indices].min(axis=1)
                if exclude_groups is not None:
                    column = np.where(np.asarray(exclude_groups) == group, np.inf, column)
                columns.append(column)
            matrix = np.column_stack(columns)
            nearest = np.sort(matrix, axis=1)[:, :self.k]
            if nearest.shape[1] != self.k or not np.isfinite(nearest).all():
                raise ValueError('too few independent reference lists for a class')
            output.append(nearest.mean(axis=1))
        return np.column_stack(output)

    def knn_probability(self, x, exclude_groups=None):
        distances = self.distances(x)
        nearest_indices = np.column_stack([
            indices[np.argmin(distances[:, indices], axis=1)] for indices in self.indices])
        nearest_distances = np.take_along_axis(distances, nearest_indices, axis=1)
        if exclude_groups is not None:
            nearest_distances[np.asarray(exclude_groups)[:, None] == self.unique_groups] = np.inf
        order = np.argsort(nearest_distances, axis=1, kind='stable')[:, :self.k]
        if not np.isfinite(np.take_along_axis(nearest_distances, order, axis=1)).all():
            raise ValueError('too few reference lists')
        labels = self.y[np.take_along_axis(nearest_indices, order, axis=1)]
        return labels.mean(axis=1)

    def work(self, variant):
        # Declared heterogeneous units, not CPU/bit-operation counts. Includes
        # standardization, all pairwise differences/squares/sums/square roots,
        # class/list minima, and full sort (an intentionally transparent scale).
        n, d = self.x.shape
        g = len(self.unique_groups)
        sorts = g * max(1, g.bit_length()) * (1 if variant == 'knn' else 2)
        return 3*d + n*(3*d+1) + 2*n + sorts + 2*self.k


def design(x, bank, variant, exclude_groups=None):
    x = np.asarray(x, dtype=float)
    if variant == 'baseline':
        return x
    distances = bank.class_distances(x, exclude_groups)
    if variant == 'hard':
        return np.column_stack((x, distances[:, 0]))
    if variant == 'both':
        return np.column_stack((x, distances))
    if variant == 'distances':
        return distances
    raise ValueError(variant)


class NeighborModel:
    """Adapter lets the unchanged paid pool runner compute proximity online."""
    def __init__(self, bank, variant, fitted=None):
        self.bank, self.variant, self.fitted = bank, variant, fitted

    def predict_proba(self, x):
        if self.variant == 'knn':
            p = self.bank.knn_probability(x)
            return np.column_stack((1-p, p))
        return self.fitted.predict_proba(design(x, self.bank, self.variant))
