import ast
import importlib
import importlib.machinery
import sys

_default_pathfinder = sys.meta_path[-1]

def _call_with_frames_removed(f, *args, **kwds):
    """remove_importlib_frames in import.c will always remove sequences
    of importlib frames that end with a call to this function
    Use it instead of a normal call in places where including the importlib
    frames introduces unwanted noise into the traceback (e.g. when executing
    module code)
    """
    return f(*args, **kwds)


class PycacheLoader(importlib.machinery.SourceFileLoader):
    def source_to_code(self, data, path, *, _optimize=-1):
        source = importlib._bootstrap.decode_source(data)
        i = 0
        while True:
            literal = '_EMPTY_SET_LITERAL_{}_'.format(i)
            if not literal in source:
                break
            i += 1
        source = source.replace('∅', literal)
#        tree = _call_with_frames_removed(compile, source, path, 'exec',
#                                         dont_inherit=True,
#                                         optimize=_optimize,
#                                         flags=ast.PyCF_ONLY_AST)
        #tree = FixEmptySet(literal).visit(tree)
        return _call_with_frames_removed(compile, tree, path, 'exec',
                                         dont_inherit=True,
                                         optimize=_optimize)

class PycacheFinder(type(_default_pathfinder)):
    @classmethod
    def find_module(cls, fullname, path=None):
        spec = _default_pathfinder.find_spec(fullname, path)
        if not spec:
            return spec
        loader = spec.loader
        loader.__class__ = PycacheLoader
        return loader

sys.meta_path[-1] = PycacheFinder
