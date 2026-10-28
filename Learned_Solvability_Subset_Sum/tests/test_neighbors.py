import unittest

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from neighbor_experiment import calibrated_bundle, inference_work, normalized_signature, probabilities, score
from neighbor_models import NeighborModel, ReferenceBank, design


class NeighborTests(unittest.TestCase):
    def setUp(self):
        # Each list contains both outcomes; repeated targets must not get extra votes.
        self.x=np.array([[v] for v in (0,1,3,4,8,9,15,16)],dtype=float)
        self.y=np.array([0,1]*4)
        self.groups=np.array(['a','a','b','b','c','c','d','d'])
        self.bank=ReferenceBank(self.x,self.y,self.groups,k=2)

    def test_entire_own_list_excluded_and_class_distances_exact(self):
        distances=self.bank.class_distances([[0]],exclude_groups=['a'])[0]
        scale=self.bank.scaler.scale_[0]
        np.testing.assert_allclose(distances,[(3+8)/2/scale,(4+9)/2/scale])
        # Excluding just the row would incorrectly retain its easy sibling at 1.
        self.assertGreater(distances[1],1/scale)

    def test_repeated_targets_do_not_count_as_distinct_neighbor_lists(self):
        distances=self.bank.class_distances([[0]])[0]
        scale=self.bank.scaler.scale_[0]
        np.testing.assert_allclose(distances,[(0+3)/2/scale,(1+4)/2/scale])
        x=np.vstack([self.x,[[0],[0]]])
        bank=ReferenceBank(x,np.r_[self.y,0,0],np.concatenate((self.groups,['a','a'])),k=2)
        np.testing.assert_allclose(bank.class_distances([[0]])[0]*bank.scaler.scale_[0],distances*scale)

    def test_nearest_list_vote_and_group_exclusion(self):
        self.assertEqual(self.bank.knn_probability([[1]])[0],.5)
        self.assertEqual(self.bank.knn_probability([[1]],['a'])[0],0)

    def test_adapter_matches_offline_design_and_cost_includes_lookup(self):
        for arm,dimension in [('hard',2),('both',3),('distances',2)]:
            x=design(self.x,self.bank,arm,self.groups)
            self.assertEqual(x.shape,(8,dimension))
            fitted=make_pipeline(StandardScaler(),LogisticRegression()).fit(x,self.y)
            model=NeighborModel(self.bank,arm,fitted)
            np.testing.assert_allclose(model.predict_proba(self.x),fitted.predict_proba(design(self.x,self.bank,arm)))
            bundle=calibrated_bundle(model,self.x,self.y,dimension)
            self.assertTrue(np.isfinite(probabilities(bundle,self.x)).all())
            saved=dict(bank=self.bank,bundles={arm:bundle})
            self.assertGreater(inference_work(saved,arm),6*dimension+20)

    def test_reference_groups_need_enough_independent_lists(self):
        bank=ReferenceBank(self.x,self.y,self.groups,k=4)
        with self.assertRaises(ValueError):
            bank.class_distances([[0]],['a'])

    def test_scaled_duplicates_and_hard_metrics(self):
        self.assertEqual(normalized_signature([3,6,12]),normalized_signature([24,6,12]))
        result=score([1,1,0,0],[.9,.4,.2,.8])
        self.assertEqual(result['confusion_easy_hard'],[[1,1],[1,1]])
        self.assertEqual(result['hard_recall'],.5)
        self.assertEqual(result['hard_precision'],.5)


if __name__=='__main__':
    unittest.main()
