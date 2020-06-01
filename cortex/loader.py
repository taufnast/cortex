import importlib
import pathlib
import sys


def load_modules(root):
    """
    traverse supplied directory and import all the python modules excluding those
    which names start with _
    :param root: path to directory
    :return: list of modules names
    """
    root = pathlib.Path(root).absolute()
    sys.path.insert(0, str(root.parent))
    imported_modules = []

    for path in root.iterdir():
        if path.name.startswith('_') or not path.suffix == '.py':
            continue
        mod = f'{root.name}.{path.stem}'
        imported_modules.append(mod)
        # print(path.stem)
        importlib.import_module(mod, package=root.name)
    return imported_modules
