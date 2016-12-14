from importlib.machinery import PathFinder, SourceFileLoader
import ast
import sys
import pycache
import pdb
import inspect


# TODO: pyc files?
class Finder(PathFinder):
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        spec = super(Finder, cls).find_spec(fullname, path, target)
        if spec is None:
            return None

        spec.loader = Loader(spec.loader.name, spec.loader.path)
        return spec


class Loader(SourceFileLoader):
    def exec_module(self, module):
        source = inspect.getsource(module)
        tree = ast.parse(source)
        transformer = pycache.WrapModule('pycache.memoize_all')
        transformer.visit(tree)
        code = compile(tree, '', 'exec')
        exec(code, module.__dict__, module.__dict__)

    def __init__(self, *args):
        super(SourceFileLoader, self).__init__(*args)


sys.meta_path.insert(0, Finder)
