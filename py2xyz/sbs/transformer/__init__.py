
import ast
import abc
import logging
import symtable
from typing import (
    Iterable,
    Mapping,
    NewType,
    Tuple,
    Union,
)
from itertools import zip_longest

logger = logging.getLogger(__name__)

from py2xyz import (
    dump,
)

from py2xyz.sbs.ast import (
    Package,
    Parameter,
    Constant,
    Output,
    FunctionGraph,
    BinaryOperation,
    NumericalOperator,
    Reference,
)

SymbolName  = NewType('SymbolName', str)
SymbolScope = NewType('SymbolScope', int)
Symbol = ast.AST

# inheriting from symtable.SymbolTable is artifical as we are re-implementating most functions, but at least the intent is clear that we implement a symboltable
class SymbolTable(symtable.SymbolTable, abc.ABC):
    def __init__(self, name, type):
        self.id = None
        self.name = name
        self.type = type
        self.symbols = { }
        self.children = []
        self.nested = False

    def get_id(self):
        """Return the type of the symbol table. Possible values are 'class', 'module', and 'function'."""
        return self.id

    def get_type(self):
        """Return the type of the symbol table. Possible values are 'class', 'module', and 'function'."""
        return self.type

    def get_name(self):
        """Return the table’s name. This is the name of the class if the table is for a class, the name of the function if the table is for a function, or 'top' if the table is global (get_type() returns 'module')."""
        return self.name

    def is_optimized(self):
        """Return True if the locals in this table can be optimized."""
        return False

    def is_nested(self):
        """Return True if the block is a nested class or function."""
        return self.nested

    def has_children(self):
        """Return True if the block has nested namespaces within it. These can be obtained with get_children()."""
        return len(self.children) > 0

    def has_exec(self):
        """Return True if the block uses exec."""
        return False

    def get_identifiers(self):
        """Return a list of names of symbols in this table."""
        return self.symbols

    def lookup(self, name):
        """Lookup name in the table and return a Symbol instance."""
        return self.symbols[name]

    def get_symbols(self):
        """Return a list of Symbol instances for names in the table."""
        return

    def get_children(self):
        """Return a list of the nested symbol tables."""
        return self.children

    def update(self, symbol_datas : Mapping[SymbolName, Symbol]):
        self.symbols.update(symbol_datas)

class FunctionSymbolTable(SymbolTable):
    def __init__(self, name):
        super().__init__(name, 'function')

    def get_parameters():
        pass

    def get_locals():
        pass

    def get_globals():
        pass

    def get_frees():
        pass

class UnsupportedASTNode(RuntimeError):
    pass

class UnsupportedTranspilerProcessing(RuntimeError):
    pass

class Transpiler(ast.NodeTransformer):
    def generic_visit(self, node):
        raise UnsupportedASTNode(dump(node))

class FunctionGraphNodesTranspiler(Transpiler):

    def __init__(self, name):
        super().__init__()
        self.symbol_table = FunctionSymbolTable(name)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            return Reference(to=self.symbol_table.lookup(node.id))
            # return Get(symbol=node.id)
        else:
            raise UnsupportedTranspilerProcessing(f'Unexpected node encounter during visit {dump(node)}')

    def visit_Num(self, node):
        return Constant(value=node.n)

    def visit_Add(self, node):
        return NumericalOperator.Add

    def visit_Mod(self, node):
        return NumericalOperator.Mod

    def visit_Pow(self, node):
        return NumericalOperator.Pow

    def visit_Tuple(self, node):
        count = len(node.elts)
        if count not in {1, 2, 3, 4}:
            raise UnsupportedASTNode(f'Tuple count unusupported : {dump(node)}')

        subnodes = list(map(self.visit, node.elts))

        are_subnodes_constants = all(
            isinstance(_, Constant)
            for _ in subnodes
        )
        if are_subnodes_constants:
            return Constant(value=[_.value for _ in subnodes])
        else:
            # TODO if not constants, we need to transpile to Vector XYZW or Cast operator
            raise UnsupportedASTNode(f'Tuple elements unusupported : {dump(node)}')

    def visit_BinOp(self, node):
        return BinaryOperation(
            left=self.visit(node.left),
            right=self.visit(node.right),
            operator=self.visit(node.op),
        )

    def visit_Return(self, node):
        return Output(expression=self.visit(node.value))

class FunctionGraphTranspiler(Transpiler):

    def __init__(self):
        self.body_transpiler = None

    def visit_FunctionDef(self, node : ast.FunctionDef):
        assert self.body_transpiler is None
        self.body_transpiler = FunctionGraphNodesTranspiler(node.name)
        return FunctionGraph(
            identifier=node.name,
            parameters=self.visit_arguments(node.args),
            nodes=self.visit_body(node.body),
        )

    def visit_arguments(self, node : ast.arguments):
        if node.vararg is not None:
            raise UnsupportedASTNode(f'arguments.varag : {dump(node.vararg)}')

        def type_from_annotation(annotation):
            if isinstance(annotation, ast.Name):
                return annotation.id
            else:
                return None

        def type_from_default(node):
            if isinstance(node, ast.Num):
                return node.n.__class__.__name__
            else:
                return None

        parameters = [
            Parameter(identifier=subnode.arg, type=type_from_annotation(subnode.annotation), value=None)
            for subnode in node.args
        ]

        for parameter, node_default in zip(parameters[-len(node.defaults):], node.defaults):
            parameter.value = node_default
            if (node_default is not None) and (parameter.type is None):
                parameter.type = type_from_default(node_default)

            # TODO make sure node_default is constant expression
            # TODO deduce type from node_default

        self.body_transpiler.symbol_table.update({
            parameter.identifier: parameter
            for parameter in parameters
        })

        return parameters

    def visit_body(self, nodes):
        return list(filter(None, map(self.body_transpiler.visit, nodes)))

class PackageTranspiler(Transpiler):

    def visit_Module(self, node : ast.Module):
        node_package_description = next((
            # subnode
            subnode
            for subnode in ast.iter_child_nodes(node)
            if isinstance(subnode, ast.Expr)
            if isinstance(subnode.value, ast.Str)
        ), None)
        if node_package_description is not None:
            node.body.remove(node_package_description)
        return Package(
            description=ast.literal_eval(node_package_description.value) if node_package_description else None,
            content=list(filter(None,(
                self.visit(node)
                for node in ast.iter_child_nodes(node)
            )))
        )

    def visit_FunctionDef(self, node : ast.Module):
        return FunctionGraphTranspiler().visit(node)
