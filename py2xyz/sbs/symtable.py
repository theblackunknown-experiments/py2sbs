
import ast
import abc
import pprint
import logging
import symtable
import functools
from typing import (
    Iterable,
    Mapping,
    NewType,
    Tuple,
    Union,
)

logger = logging.getLogger(__name__)

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

    def update(self, symbol_datas):
        self.symbols.update(symbol_datas)

    def __str__(self):
        return pprint.pformat(self.symbols)

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
