import importlib
import pathlib
import sys


def load_modules(root):
    root = pathlib.Path(root).absolute()
    sys.path.insert(0, str(root.parent))
    imported_modules = []

    for path in root.iterdir():
        if path.name.startswith('_') or not path.suffix == '.py':
            continue
        mod = f'{root.name}.{path.stem}'
        imported_modules.append(mod)
        print(mod)
        importlib.import_module(mod, package=root.name)
    return imported_modules
