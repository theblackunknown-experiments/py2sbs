
import ast
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

from py2sbs.ast import (
    dump,
)

class NodeNotSupported(RuntimeError):
    pass

class Generator(ast.NodeVisitor):
    def __init__(self, path : Path):
        self.path = path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def generic_visit(self, node):
        raise NodeNotSupported(dump(node))
