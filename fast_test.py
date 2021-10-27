import sys 
from typing import List
import logging


from lark import Lark, logger, Token
from lark.exceptions import UnexpectedToken, UnexpectedCharacters
from lark.indenter import Indenter

logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)

class TreeIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types : List[str]= []
    CLOSE_PAREN_types : List[str] = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 4

with open("PyDayuri/grammar.lark") as grammar:
  p = Lark(grammar,parser="lalr", postlex=TreeIndenter(), debug=True, maybe_placeholders=True, cache=False)

def ignore_errors(e):
    return False


with open(sys.argv[1]) as f :
  f2 = f.read()
  try :
    parsed = p.parse(f2, on_error= ignore_errors)
    print(f2)
    print()
    print(parsed.pretty())
  except UnexpectedToken as e:
      print(e.get_context(f2))
      print(e)
  except UnexpectedCharacters as e:
      print(e)

