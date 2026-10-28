"""Run a grouped Paper VI script using its original command-line arguments."""
import ast
import importlib
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from Learned_Solvability_Subset_Sum.experiments._layout import activate, LAYOUT, ROOT

if len(sys.argv)<2:
    raise SystemExit('Usage: python Learned_Solvability_Subset_Sum/run.py SCRIPT [arguments]')
name = Path(sys.argv[1]).stem
if name not in LAYOUT['module_locations']:
    raise SystemExit('Unknown script: '+name)
activate()
module = importlib.import_module(name)
sys.argv = [module.__file__,*sys.argv[2:]]
tree = ast.parse((ROOT/LAYOUT['module_locations'][name]).read_bytes())
for node in tree.body:
    if isinstance(node,ast.If) and ast.dump(node.test)==ast.dump(ast.parse('__name__ == "__main__"',mode='eval').body):
        exec(compile(ast.Module(body=node.body,type_ignores=[]),module.__file__,'exec'),module.__dict__)
        break
else:
    raise SystemExit('This module has no command-line entry point: '+name)
