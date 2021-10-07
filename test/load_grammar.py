from lark import Lark

with open("src/grammar.lark") as f :
  grammar_file = f.read()

def get_parser(**args):
  parser = Lark(grammar_file, parser="lalr", debug=True, **args)
  return parser.parse

