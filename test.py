import sys 

import logging


from lark import Lark, logger
from lark.indenter import Indenter

logger.setLevel(logging.DEBUG)

class TreeIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 8

with open("src/grammar.lark") as f:
  p = Lark(f,parser="lalr", postlex=TreeIndenter(), debug=True)

#with open(sys.argv[1]) as f :
#  f2 = f.read()
#  parsed = p.parse(f2)
#
#print(f2)
#print()
#print(parsed.pretty())
