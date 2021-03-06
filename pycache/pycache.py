import matplotlib.pyplot as plt
import operator
from functools import reduce
import numpy as np
import xxhash
import pickle
import dill
import ujson
import sys
import pdb
import ast
import inspect
import astor
from meta.decompiler import decompile_func
import logging
logging.basicConfig(filename = 'pycache.log', level = logging.DEBUG)

# Can equal 'performance' or 'correctness'
caching_strategy = 'correctness'


class MemoCache:
    """
    Provides an interface to the memoization cache for one function.
    """
    def __init__(self, callnode, vars = True, code = True, global_env = {}):
        # TODO: figure out namespace issues
        self.vars = vars
        self.code = code
        self.cache = {}
        self.global_env = global_env
        if self.vars or self.code:
            deps = DependencyWalk(global_env = global_env)
            deps.visit(callnode)
            # TODO: insert code here that loads the persistent cache from disk
            self.code_hash = obj_digest(deps.code_hashes)
            #self.code_hash = hash_obj(deps.code_hashes)
            self.global_deps = deps.globals
        # TODO: add a mechanism for including and updating file dependencies
        # self.file_deps = []

    def update_code_and_global_deps(self, callnode):
        if self.vars or self.code:
            deps = DependencyWalk(global_env = self.global_env)
            deps.visit(callnode)
            # TODO: why does this code hash change over repeated calls with the same arguments?
            #print(self.code_hash)
            new_code_hash = obj_digest(deps.code_hashes)
            new_global_deps = deps.globals
            # TODO: this will fail if there's a discrepancy between the module prefixes between
            # new_global_deps and self.global_deps
            if new_code_hash != self.code_hash or new_global_deps != self.global_deps:
                self.cache = {}
                self.code_hash = new_code_hash
                self.global_deps = new_global_deps

    def _get_key(self, *args, **kwargs):
        arghash = obj_digest((args, kwargs))
        if self.vars:
            varhash = obj_digest([var for var in self.global_deps])
            return obj_digest(arghash + varhash)
        else:
            return obj_digest(arghash)

    def lookup(self, *args, **kwargs):
        return self.cache[self._get_key(*args, **kwargs)]

    def insert(self, value, *args, **kwargs):
        self.cache[self._get_key(*args, **kwargs)] = value

class DependencyWalk(ast.NodeVisitor):
    """
    Walk AST to find code and global variable dependencies.
    """
    def __init__(self, module_prefix = [], global_env = {}):
        self.code_hashes = set()
        self.globals = set()
        self.module_prefix = module_prefix # list of strings
        self.global_env = global_env

    def lookup_obj(self, name_path, module_prefix = []):
        """
        Look up an object based on its name and the current module prefix.
        """
        return lookup_obj(name_path, self.module_prefix, global_env = self.global_env)

    # TODO: resolve global variable deps
    def visit_Call(self, node):
        from types import FunctionType, MethodType
        name_path = attribute_path(node.func)
        try:
            if isinstance(self.lookup_obj(name_path), FunctionType):
            # Check if function is in a different module
                raw_source = self.lookup_obj(name_path)._source
                source_tree = decode_ast(raw_source)
                if len(name_path) > 1:
                    start_tree = ast.parse(source_tree)
                    new_visitor = DependencyWalk(self.module_prefix + name_path[:-1],
                                                 global_env = self.global_env)
                    new_visitor.visit(start_tree)
                    self.code_hashes |= new_visitor.code_hashes
                    self.globals |= new_visitor.globals
                else:
                    self.code_hashes.add(obj_digest(raw_source))
            # If this is a method call the best we can do is just hash the object.
            # If we want to track object dependencies, this has to be
            # done by modifying the class.
            elif isinstance(self.lookup_obj(name_path), MethodType):
                self.code_hashes.add(raw_source)
            else:
                logging.debug("Non-function or method node: %s" % str(node))
        except (NameError, SyntaxError) as e:
            raise
            # TODO: track down the source of syntax errors
            # We expect this exception raised on every call involving an object
            # in an unreachable scope (i.e. lexical closures and class instance
            # variables)
            logging.debug("Callable lookup failed: %s" % e)
        # Recursively visit the child nodes
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        name = node.name
        hash = obj_digest(self.lookup_obj([name]))
        # To avoid infinite recursion, make sure we haven't already seen this
        # function
        if hash not in self.code_hashes:
            self.code_hashes.add(hash)
            self.generic_visit(node)

def lookup_obj(name_path, module_prefix = [], global_env = {}):
    """
    Look up an object based on its name and the current module prefix.
    """
    ref = '.'.join(module_prefix + name_path)
    if global_env:
        return eval(ref, global_env, global_env)
    else:
        return eval(ref)


def simplememo(f):
    """Basic memoization wrapper"""
    cache = {}
    def new_f(*args):
        if args not in cache:
            cache[args] = f(*args)
        return cache[args]
    return new_f

def encode_ast(tree):
    return dill.dumps(tree).decode('cp437')

# TODO: why doesn't this improve runtime?
#@simplehashmemo
def decode_ast(string):
    return dill.loads(string.encode('cp437'))

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

count = {'c': 0}
def serialize(obj):
    """
    Try fast (but limited) serialization on non-callable objects.
    If it fails, try pickle and then finally dill.
    """
    if callable(obj):
        return dill.dumps(obj)
    try:
        return pickle.dumps(obj)
    except:
        return dill.dumps(obj)

def obj_digest(to_digest):
    return xxhash.xxh64(serialize(to_digest)).hexdigest()

def hash_obj(obj):
    u"""
    return a hash of any python object
    """

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

def search_decorator_list(defnode):
    """
    Return true if at least one of a FunctionDef node's decorators is a
    function defined in pycache.
    """
    for node in defnode.decorator_list:
        # TODO: make this prettier
        if type(node) == ast.Call and type(node.func) == ast.Attribute:
            if 'pycache' == node.func.value.id:
                return True
    return False

class WrapModule(ast.NodeVisitor):
    """
    Modify AST by "wrapping" function definitions.
    """
    def __init__(self, wrapper):
        self.wrapper = wrapper

    def visit_Module_or_FunctionDef(self, node):
        new_body = []
        for i, bnode in enumerate(node.body):
            new_body.append(bnode)
            if type(bnode) == ast.FunctionDef:
                # Rebind the function to its wrapped version if the user hasn't explicitly
                # annotated it.
                if not search_decorator_list(bnode):
                    bnode.decorator_list.insert(0, ast.parse(self.wrapper).body[0].value)
                new_body.append(
                    ast.fix_missing_locations(
                        ast.Assign(targets=[ast.Attribute(value = ast.Name(id = bnode.name, ctx = ast.Load()),
                                                          attr = '_source', ctx = ast.Store())],
                                   value = ast.Str(s = encode_ast(bnode)))))

        node.body = new_body
        self.generic_visit(node)

    def visit_Module(self, node):
        node.body.insert(0, ast.Import(names=[ast.alias(name='pycache', asname=None)]))
        ast.fix_missing_locations(node)
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



def get_globals():
    return globals()

def memoizer(memo_args = True, memo_vars = True, memo_code = True, custom_cache = '[]'):
    """
    Generate a memoizing decorator that takes into account zero or more of (1)
    function arguments, (2) local and global variables, and (3) code
    dependencies.  If none of these is selected, no memoization is done.
    """
    def inner_memoizer(f):
        """ Main memoization wrapper"""
        state = {'memocache': None, 'tree': None}

        def new_f(*args, **kwargs):
            cache = state['memocache']
            loc = locals()
            loc.update(kwargs)
            cc = eval(custom_cache, globals(), loc)

            # TODO: parse the tree in parent scope to avoid wasteful repeated
            # computation
            if state['tree'] == None:
                state['tree'] = ast.Module(body = decode_ast(new_f._source).body)

            if cache is None:
                global_env = f.__globals__
                cache = state['memocache'] = MemoCache(state['tree'], global_env = global_env,
                                                       vars = memo_vars, code = memo_code)
            elif caching_strategy == 'correctness':
                cache.update_code_and_global_deps(state['tree'])
            try:
                if memo_args: # Include function arguments in cache key
                    new_args = list(args) + cc
                    return cache.lookup(*new_args, **kwargs)
                else: # Exclude them
                    return cache.lookup(cc)
            except KeyError:
                result = f(*args, **kwargs)
                if memo_args:
                    args = list(args) + cc
                    cache.insert(result, *args, **kwargs)
                else:
                    cache.insert(result, cc)
                return result

        def identity(*args, **kwargs):
            return f(*args, **kwargs)

        if (not memo_args and not memo_vars and not memo_code and custom_cache == '[]'):
            return identity
        else:
            return new_f
    return inner_memoizer

# Default memoization wrapper
memoize_all = memoizer(memo_args = True, memo_vars = True, memo_code = True, custom_cache = '[]')

def eval_node(node, context = {}):
    expr = ast.Expression(node)
    code = compile(expr, '', 'eval')
    return eval(code, globals(), context)

def exec_node(node, glob = None, context = {}):
    """expects a Module node"""
    code = compile(node, '', 'exec')
    if glob is None:
        glob  = globals()
    return exec(code, glob, context)


def p_ast(obj):
    source = inspect.getsource(obj)
    tree = ast.parse(source)
    print(astor.dump(tree))
