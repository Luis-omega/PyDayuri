import sys 
from typing import Dict
import logging


from lark import Lark, logger
from lark.exceptions import UnexpectedToken, UnexpectedCharacters
#from lark.indenter import Indenter
from PyDayuri.indenter import Indenter,IndentType, IndenterError

#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

class TreeIndenter(Indenter):
    REGULAR_INDENT = ("_INDENT", "_DEDENT", "_NL")
    INDENT_BLOCKS = {"_LET":(IndentType.at_next, "_IN", "_LET_SEPARATOR")}
    PRODUCE_INDENT:Dict[str, IndentType] = dict()


with open("examples/indenter.lark") as f:
  p = Lark(f,parser="lalr", lexer="standard", postlex=TreeIndenter(), debug=True)

with open(sys.argv[1]) as f :
  f2 = f.read()
  try :
    parsed = p.parse(f2)
    print(f2)
    print()
    print(parsed.pretty())
  except IndenterError as e:
      print(e.pre_msg)
      print(UnexpectedToken.get_context(e.token,f2))
      print(e.post_msg)
  except UnexpectedToken as e:
      print(e.get_context(f2))
      print(e)
  except UnexpectedCharacters as e:
      print(e)

