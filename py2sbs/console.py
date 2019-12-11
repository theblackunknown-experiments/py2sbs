#!/usr/bin/env python3

import ast
import logging
import argparse

from pathlib import Path

logger = logging.getLogger(__name__)

from py2sbs import (
    __version__ as py2sbsversion,
    __doc__ as py2sbsdoc,
)

from py2sbs.ast import (
    dump,
)

from py2sbs.codegen import (
    Generator as SBSGenerator,
)

SETTINGS_FOLDER = Path.home() / '.py2sbs' / py2sbsversion

def main():
    parser = argparse.ArgumentParser(description=py2sbsdoc)
    parser.add_argument(
        'source_file',
        type=argparse.FileType('rt', encoding='utf-8'),
        help='source filepath to process (supported extensions: .py)',
    )

    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('wt', encoding='utf-8'),
        help='source filepath to process (supported extensions: .py)',
    )

    parser.add_argument(
        '-v', '--verbose',
        help='Make runtime more verbose, more "v", more fun',
        action='count',
        default=0,
    )

    parser.add_argument(
        '--pretty-print',
        help='Print source AST instead of transpiling',
        action='store_true',
    )

    arguments = parser.parse_args()

    if arguments.source_file is None:
        logger.error(f'missing <source_file>')
        return 1

    if arguments.verbose >= 1:
        logger.setLevel( logging.DEBUG )

    try:
        ast_root_node = ast.parse(
            source=arguments.source_file.read(),
            filename=getattr(arguments.source_file, 'name', '<string>'),
        )

        if arguments.pretty_print:
            logger.info(dump(ast_root_node))
            return 0

        with SBSGenerator(Path(arguments.output.name)) as generator:
            generator.visit(ast_root_node)

        return 0
    except (ValueError, SyntaxError) as e:
        logger.error(f'Invalid DSL : {e}')
        return -1

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='[{name}] {message}',
        datefmt=None,
        style='{'
    )

    import sys
    sys.exit(main())
