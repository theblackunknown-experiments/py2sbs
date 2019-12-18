#!/usr/bin/env python3

import ast
import logging
import argparse
import tempfile

from pathlib import Path

logger = logging.getLogger(__name__)

from py2xyz import (
    __name__ as modulename,
    __version__ as moduleversion,
    __doc__ as moduledoc,
    dump,
)

from py2xyz.sbs.transformer import (
    TranspilerNodeTransformer as SubstanceTranspiler,
)

SETTINGS_FOLDER = Path.home() / f'.{modulename}' / moduleversion

def main():
    parser = argparse.ArgumentParser(description=moduledoc)
    parser.add_argument(
        'source_file',
        type=argparse.FileType('rt', encoding='utf-8'),
        help='source filepath to process (supported extensions: .py)',
    )

    parser.add_argument(
        '-t', '--target',
        choices=[
            'sbs',
        ],
        help='target language',
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

    if arguments.verbose >= 2:
        logger.setLevel( logging.DEBUG )
    elif arguments.verbose >= 1:
        logger.setLevel( logging.INFO )

    try:
        ast_source_root_node = ast.parse(
            source=arguments.source_file.read(),
            filename=getattr(arguments.source_file, 'name', '<string>'),
        )

        if arguments.pretty_print:
            logger.info(dump(ast_source_root_node))
            return 0

        if arguments.target == 'sbs':
            logger.info(f'Transpiling to {arguments.target}')
            transformer = SubstanceTranspiler()
            ast_target_root_node = transformer.visit(ast_source_root_node)
            print(dump(ast_target_root_node))

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
