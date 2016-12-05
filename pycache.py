import pdb
import ast
import inspect
import astor
from meta.decompiler import decompile_func
import logging
logging.basicConfig(filename = 'pycache.log', level = logging.DEBUG)

# Can equal 'performance' or 'correctness'
caching_strategy = 'performance'


def singleton(theClass):
    """ decorator to make MemoCache a singleton"""
    classInstances = {}

    def getInstance(*args, **kwargs):
        """ creating or just return the one and only class instance for a given
        function.  The singleton depends on the first parameter used in
        __init__"""
        # TODO: do something to avoid function name collisions
        funcnode = args[0].func
        key = attribute_path(funcnode)[-1]
        if key not in classInstances:
            classInstances[key] = theClass(*args, **kwargs)
        return classInstances[key]

    return getInstance

@singleton
class MemoCache:
    """
    Provides an interface to the memoization cache for one function.
    
    This class is a singleton keyed using identity of the memoized function.
    """
    def __init__(self, callnode):
        # TODO: figure out namespace issues
        deps = DependencyWalk()
        deps.visit(callnode)
        # TODO: insert code here that loads the persistent cache from disk
        self.cache = {}
        self.code_hash = hash_obj(deps.code_hashes())
        self.global_deps = deps.globals
        # TODO: add a mechanism for including and updating file dependencies
        self.file_deps = []

    def update_code_and_global_deps(self, callnode):
        deps = DependencyWalk()
        deps.visit(callnode)
        new_code_hash = hash_obj(deps.code_hashes())
        new_global_deps = deps.globals
        # TODO: this will fail if there's a discrepancy between the module prefixes between
        # new_global_deps and self.global_deps
        if new_code_hash != self.code_hash or new_global_deps != self.global_deps:
            self.cache = {}
            self.code_hash = new_code_hash
            self.global_deps = new_global_deps

    def _get_key(self, *args, **kwargs):
        arghash = hash_obj((args, kwargs))
        varhash = hash_obj([var for var in self.global_deps])
        return hash_obj(arghash + varhash)

    def lookup(self, *args, **kwargs):
        return self.cache[self._get_key(*args, **kwargs)]

    def insert(self, value, *args, **kwargs):
        self.cache[self._get_key(*args, **kwargs)] = value


class DependencyWalk(ast.NodeVisitor):
    """
    Walk AST to find code and global variable dependencies.
    """
    def __init__(self, module_prefix = []):
        self.code_hashes = set()
        self.globals = set()
        self.module_prefix = module_prefix # list of strings

    def lookup_obj(self, name_path, module_prefix = []):
        """
        Look up an object based on its name and the current module prefix.
        """
        return lookup_obj(name_path, self.module_prefix)

    # TODO: resolve global variable deps

    def visit_Call(self, node):
        from types import FunctionType, MethodType
        name_path = attribute_path(node.func)
        try:
            if isinstance(self.lookup_obj(name_path), FunctionType):
            # Check if function is in a different module
                if len(name_path) > 1:
                    start_source = inspect.getsource(self.lookup_obj(name_path))
                    start_tree = ast.parse(start_source)
                    new_visitor = DependencyWalk(self.module_prefix + name_path[:-1])
                    new_visitor.visit(start_tree)
                    self.code_hashes |= new_visitor.code_hashes
                    self.globals |= new_visitor.globals
                else:
                    self.code_hashes.add(hash_obj(self.lookup_obj(name_path)))
            # If this is a method call the best we can do is just hash the object.
            # If we want to track object dependencies, this has to be
            # done by modifying the class AST.
            elif isinstance(self.lookup_obj(name_path), MethodType):
                self.code_hashes.add(hash_obj(self.lookup_obj(name_path[:-1])))
            else:
                logging.debug("Non-function or method node: %s" % str(node))
        except NameError as e:
            # We expect this exception raised on every call involving an object
            # outside of the current lexical scope.
            logging.debug("Callable lookup failed: %s" % e)
        # Recursively visit the child nodes
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        name = node.name
        self.code_hashes.add(hash_obj(self.lookup_obj([name])))
        self.generic_visit(node)

def lookup_obj(name_path, module_prefix = []):
    """
    Look up an object based on its name and the current module prefix.
    """
    return eval('.'.join(module_prefix + name_path))

def callnode_get_functionnode(callnode):
    name_path = attribute_path(callnode.func)
    start_source = inspect.getsource(lookup_obj(name_path))
    return ast.parse(start_source)


def attribute_path(node):
    """
    Given an Attribute node containing either an Attribute node or a Name node,
    return the path to the object (i.e. in the format ['this', 'nested',
    'function'] for object this.nested.function)
    """
    if type(node) == ast.Name:
        return [node.id]
    else:
        return attribute_path(node.value) + [node.attr]

def test_eval_attribute():
    node = ast.parse('other.third.bazbar').body[0].value
    assert attribute_path(node) == ['other', 'third', 'bazbar']


def hash_obj(obj):
    u"""
    return a hash of any python object
    """
    import hashlib
    import dill
    import operator
    from functools import reduce
    import numpy as np
    def obj_digest(to_digest):
        return hashlib.sha1(dill.dumps(to_digest)).hexdigest()

    def iter_digest(to_digest):
        return obj_digest(reduce(operator.add, list(map(hash_obj, to_digest))))

    if (not isinstance(obj, np.ndarray)) and hasattr(obj, u'__iter__') and (len(obj) > 1):
        if isinstance(obj, dict):
            return iter_digest(iter(obj.items()))
        else:
            return iter_digest(obj)
    else:
        # Functions receive special treatment, such that code changes alter
        # the hash value
        if hasattr(obj, u'__call__'):
            try:
                return obj_digest(ast.dump(decompile_func(obj)))
            # This covers an exception that happens in meta.decompiler under
            # certain situations. TODO: replace this workaround with something
            # better.
            except IndexError:
                return obj_digest(dill.dumps(obj))
        else:
            return obj_digest(obj)
    

def wrap_call(call_node, wrapper):
    import copy
    call_node = copy.deepcopy(call_node)
    subtree =\
        ast.Call(
            func = ast.Name(id = wrapper.__name__, ctx = ast.Load()),
            args = [call_node.func],
            keywords = []
        )
    call_node.func = ast.fix_missing_locations(subtree)
    return call_node

# TODO: debug
import copy
class WrapModule(ast.NodeTransformer):
    def __init__(self, wrapper):
        self.wrapper = wrapper

    def visit_Module_or_FunctionDef(self, node):
        node = copy.deepcopy(node)
        new_body = []
        for i, node in enumerate(node.body):
            new_body.append(node)
            if type(node) == ast.FunctionDef:
                print ('wrapping a funtion')
                new_body.append(
                    ast.fix_missing_locations(
                        ast.Assign(targets=[ast.Name(id = node.name)],
                               value = ast.Call(
                                   func = ast.Name(id = self.wrapper.__name__, ctx = ast.Load()),
                                   args = [ast.Name(id = node.name)],
                                   keywords = []
                               ),
                               args = [ast.Name(id = node.name)],
                               keywords = []
                               )))
        node.body = new_body
        self.generic_visit(node)
        return node

    def visit_Module(self, node):
        return self.visit_Module_or_FunctionDef(node)

    def visit_FunctionDef(self, node):
        return self.visit_Module_or_FunctionDef(node)

class MemoStack:
    def __init__(self):
        self.stack = []

    def push(self, elt):
        self.stack.append(elt)

    def peek(self):
        return self.stack[-1]

    def pop(self):
        return self.stack.pop()


def simplememo(f):
    """Basic memoization wrapper"""
    cache = {}
    def new_f(*args):
#        print(args)
#        print(f)
        if args not in cache:
            cache[args] = f(*args)
        return cache[args]
    return new_f

def eval_node(node, context = {}):
    expr = ast.Expression(node)
    code = compile(expr, '', 'eval')
    return eval(code, globals(), context)

def exec_node(node, context = {}):
    """expects a Module node"""
    code = compile(node, '', 'exec')
    return exec(code, globals(), context)


def p_ast(obj):
    source = inspect.getsource(obj)
    tree = ast.parse(source)
    print(astor.dump(tree))
