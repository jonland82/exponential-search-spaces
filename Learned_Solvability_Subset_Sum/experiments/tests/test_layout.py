"""Folder grouping must preserve stored hashes and serialized model imports."""
import hashlib
from pathlib import Path
import unittest

import joblib

from _layout import LAYOUT, PACKAGE, ROOT, OriginalPaths, activate


class FollowupLayoutTests(unittest.TestCase):
    def test_frozen_sources_and_models_resolve_after_relocation(self):
        studies = activate()
        for name in ('geometric','pruning'):
            output = PACKAGE/f'results/{name}_20261028'
            studies[name].verify(output)
            saved = joblib.load(output/'models.joblib')
            self.assertIn('bundles',saved)
        for logical,digest in LAYOUT['original_sha256'].items():
            if logical.endswith('.py') or logical.endswith('_PROTOCOL.md'):
                self.assertEqual(hashlib.sha256((OriginalPaths(ROOT)/logical).read_bytes()).hexdigest(),digest)

    def test_virtual_roots_remain_pathlike_for_new_source_snapshots(self):
        root = OriginalPaths(ROOT)
        here = OriginalPaths(PACKAGE)
        for logical,actual in LAYOUT['source_locations'].items():
            self.assertEqual((root/logical).physical(),ROOT/actual)
            self.assertEqual((here/Path(logical).name).physical(),ROOT/actual)
            self.assertEqual((root/logical).relative_to(root),Path(logical))
        self.assertEqual(Path(root),ROOT)
        self.assertEqual(here/'results',PACKAGE/'results')


if __name__=='__main__':
    unittest.main()
