"""Resolve the original Paper VI follow-up names after grouping their files."""
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import sys


EXPERIMENTS = Path(__file__).resolve().parent
PACKAGE = EXPERIMENTS.parent
ROOT = PACKAGE.parent
LAYOUT = json.loads((EXPERIMENTS/'LAYOUT.json').read_text(encoding='utf-8'))


class OriginalPaths(type(Path())):
    """A logical project path whose file I/O resolves recorded relocations."""
    def __init__(self, *args):
        path = Path(*args)
        if path.is_absolute():
            try:
                current = path.relative_to(ROOT).as_posix()
                original = next((old for old,new in LAYOUT['source_locations'].items() if new==current),None)
                if original:
                    path = ROOT/original
            except ValueError:
                pass
        super().__init__(path)

    def physical(self):
        path = Path(str(self))
        try:
            logical = path.relative_to(ROOT).as_posix()
        except ValueError:
            return path
        return ROOT/LAYOUT['source_locations'].get(logical,logical)

    def __fspath__(self):
        return str(self.physical())

    def open(self, *args, **kwargs):
        return self.physical().open(*args, **kwargs)

    def stat(self, *args, **kwargs):
        return self.physical().stat(*args, **kwargs)

    def resolve(self, strict=False):
        # Keep logical __file__ parents stable for older scripts and tests.
        return type(self)(Path(str(self)).absolute())


def patch_paths(module):
    for name,value in list(vars(module).items()):
        if isinstance(value,Path) and not isinstance(value,OriginalPaths):
            setattr(module,name,OriginalPaths(str(value)))
    if getattr(module,'Path',None) is Path:
        module.Path = OriginalPaths


class RelocatedSource(importlib.machinery.SourceFileLoader):
    def exec_module(self, module):
        logical = next((name for name,location in LAYOUT['source_locations'].items()
            if ROOT/location == Path(self.path)), None)
        module.__file__ = str(ROOT/logical) if logical else self.path
        exec(self.get_code(module.__name__),module.__dict__)
        patch_paths(module)
        module.__file__ = self.path


class FollowupSources(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        location = LAYOUT['module_locations'].get(fullname)
        if location is not None:
            loader = RelocatedSource(fullname,str(ROOT/location))
            return importlib.util.spec_from_file_location(fullname,ROOT/location,loader=loader)
        if fullname.startswith('Structural_Geometry_Subset_Sum.'):
            spec = importlib.machinery.PathFinder.find_spec(fullname,path,target)
            if spec and isinstance(spec.loader,importlib.machinery.SourceFileLoader):
                spec.loader = RelocatedSource(fullname,spec.origin)
            return spec
        return None


def install():
    if not any(isinstance(f,FollowupSources) for f in sys.meta_path):
        sys.meta_path.insert(0,FollowupSources())
    for name,module in list(sys.modules.items()):
        if module is not None and name.startswith('Structural_Geometry_Subset_Sum'):
            patch_paths(module)



def activate():
    if str(PACKAGE) not in sys.path:
        sys.path.insert(0,str(PACKAGE))
    install()
    pilot = importlib.import_module('run_pilot')
    pilot.ROOT = OriginalPaths(ROOT)
    geometric = importlib.import_module('geometric_experiment')
    geometric.ROOT = OriginalPaths(ROOT)
    geometric.HERE = OriginalPaths(PACKAGE)
    pruning = importlib.import_module('pruning_experiment')
    studies = {'geometric':geometric,'pruning':pruning}
    for study in studies.values():
        if getattr(study.freeze,'organized_layout',False):
            continue
        original_freeze = study.freeze

        def freeze_with_layout(output, freeze=original_freeze):
            # Only finalize a newly created freeze, before generation. Existing
            # saved protocols are never touched by this wrapper.
            freeze(output)
            protocol = json.loads((output/'protocol.json').read_text(encoding='utf-8'))
            for name in ('_layout.py','run.py','LAYOUT.json','tests/test_layout.py','../__init__.py','../run.py'):
                source = (EXPERIMENTS/name).resolve()
                destination = output/'sources'/source.relative_to(ROOT)
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,destination)
                protocol['source_hashes'][str(source.relative_to(ROOT))] = pilot.sha(source)
            (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf-8')
            (output/'protocol.sha256').write_text(pilot.sha(output/'protocol.json')+'\n')

        freeze_with_layout.organized_layout = True
        study.freeze = freeze_with_layout
    return studies


def audit_saved(name, output):
    activate()
    auditor = importlib.import_module('audit_'+name)
    original_save = auditor.save_json

    def preserve_record(path, value):
        if path.name=='VALIDATION.json' and path.exists():
            previous = json.loads(path.read_text(encoding='utf-8'))
            assert {k:v for k,v in previous.items() if k!='utc'} == {k:v for k,v in value.items() if k!='utc'}
            print('Audit passed again; original validation record preserved',flush=True)
            return
        original_save(path,value)

    auditor.save_json = preserve_record
    try:
        auditor.audit(output)
    finally:
        auditor.save_json = original_save
