
import pprint
import logging
import functools
import itertools
import collections

logger = logging.getLogger(__name__)

from py2xyz import dump

from py2xyz.sbs.ast import *

from py2xyz.sbs.symtable import FunctionSymbolTable

class Analyzer(ast.NodeVisitor):
    pass

class OverloadResolvers(Analyzer):

    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.types_per_parameter = collections.defaultdict(set)

    def analyze(self, content):
        if isinstance(content, (list, tuple)):
            return itertools.chain(*list(
                self.analyze(subnode)
                for subnode in content
            ))
        else:
            node = content
            analyzer = getattr(self, f'analyze_{node.__class__.__name__}', None)
            if analyzer is None:
                raise RuntimeError(f'No analyzer for {node}')

            return analyzer(node)

    def analyze_Output(self, node):
        yield from self.analyze(node.expression)

    def analyze_BinaryOperation(self, node):
        for left, right in node.operator.overloads():
            left_argument_types = self.validate(node.left, left)
            right_argument_types = self.validate(node.right, right)

            if (len(left_argument_types)) == 0 or (len(right_argument_types) == 0):
                logger.debug(f'invalid program with operator {node.operator}({left}, {right}) for ({dump(node.left)}, {dump(node.right)})')
                continue

            result = dict(left_argument_types)
            for key, value in right_argument_types.items():
                if key in result:
                    result[key].intersect(right_argument_types[key])
                else:
                    result[key] = right_argument_types[key]

            for key, value in self.symbol_table.items():
                if key not in result:
                    result[key] = value

            yield from itertools.product(*result.values())

    def validate(self, node, returntype):
        if isinstance(node, AST):
            validation = getattr(self, f'validate{node.__class__.__name__}', None)
            if validation is None:
                raise NotImplementedError(f'No type validation for {node}')

            return validation(node, returntype)
        else:
            raise NotImplementedError

    def validateGet(self, node, returntype):
        if self.symbol_table[node.symbol] is None:
            # logger.debug(f'return type {returntype} - valid program because {dump(node)} is variant')
            return {
                node.symbol: { returntype }
            }
        elif returntype in self.symbol_table[node.symbol]:
            # logger.debug(f'return type {returntype} - valid program because {dump(node)} is of the same type')
            return {
                node.symbol: { returntype }
            }
        else:
            return { }

def resolve_overloads(node, parameters, content):
    logger.debug(f'resolving... {dump(node)}')

    symbol_table = {
        parameter.identifier: { parameter.type } if parameter.type else None
        for parameter in parameters
    }
    if len(symbol_table) == 0:
        return []

    resolver = OverloadResolvers(symbol_table)

    logger.debug(f'symbol table        : {symbol_table}')
    overloads = list(resolver.analyze(content))
    logger.debug(f'overloads : {pprint.pformat(overloads)}')

    return overloads
