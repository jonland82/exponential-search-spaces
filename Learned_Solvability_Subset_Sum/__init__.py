"""Organized Paper VI package with compatibility for original frozen names."""
from .experiments._layout import OriginalPaths, install
import sys

sys.modules.setdefault('_layout',sys.modules[__name__+'.experiments._layout'])

install()


def resolve_source(path):
    return OriginalPaths(str(path)).physical()


def load_original(module):
    import sys
    from .experiments._layout import LAYOUT, ROOT, RelocatedSource
    location = LAYOUT['module_locations'][module]
    RelocatedSource(module,str(ROOT/location)).exec_module(sys.modules[module])
