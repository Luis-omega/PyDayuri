import unittest 

from lark import Token, Tree

from ..load_grammar import get_parser

class Path(unittest.TestCase):
  def test_path(self):
    rule_to_test = "path"
    tests  = [
    ("some",Tree(rule_to_test, [Token("IDENTIFIER","some")]))
    ,("some1.some2",Tree(rule_to_test, [
        Token("IDENTIFIER","some1")
        ,Token("IDENTIFIER","some2")
        ]))
    ,("some.asd.d8_asdf",Tree(rule_to_test, [
        Token("IDENTIFIER","some")
        ,Token("IDENTIFIER","asd")
        ,Token("IDENTIFIER","d8_asdf")
        ]))
    ,("AS.B.c",Tree(rule_to_test, [
        Token("IDENTIFIER","AS")
        ,Token("IDENTIFIER","B")
        ,Token("IDENTIFIER","c")
        ]))
    ] 
    parser = get_parser(start=rule_to_test)
    for (case,expected) in tests:
      parsed = parser(case)
      self.assertEqual(parsed, expected)

class Import(unittest.TestCase):
  def test_import(self):
    rule_to_test = "import"
    tests  = [
    ("import some",
        Tree(rule_to_test, 
            [
            Tree("path", 
                [
                Token("IDENTIFIER","some")
                ])
            ])
    )
    ,("import some1.some2",
        Tree(rule_to_test, 
        [
        Tree("path",
          [
          Token("IDENTIFIER","some1")
          ,Token("IDENTIFIER","some2")
          ])
        ])
    )
    ,("import some.asd.d8_asdf as simp1",
        Tree(rule_to_test, 
        [
        Tree("path",
          [
          Token("IDENTIFIER","some")
          ,Token("IDENTIFIER","asd")
          ,Token("IDENTIFIER","d8_asdf")
          ])
        ,Token("IDENTIFIER","simp1")
        ]))
    ] 
    parser = get_parser(start=rule_to_test)
    for (case,expected) in tests:
      parsed = parser(case)
      self.assertEqual(parsed, expected)


class PatternMatch(unittest.TestCase):
  def test_pattern_match_tuple(self):
    rule_to_test = "pattern_match_atom"
    tests  = [
    ("(a,b)",
        Tree("pattern_tuple", 
            [
            Tree("pattern_match",
              [
              Tree("pattern_maybe_constructor", 
                [
                Tree("path", [Token("IDENTIFIER", "a")])
                ])
              ])
            ,Tree("sep_by1", 
              [
              Tree("pattern_match",
                [
                Tree("pattern_maybe_constructor", 
                  [
                  Tree("path", [Token("IDENTIFIER", "b")])
                  ])
                ])
              ])
            ])
    )
    ,("(some,things,to,test)",
        Tree("pattern_tuple", 
            [
            Tree("pattern_match",
              [
              Tree("pattern_maybe_constructor", 
                [
                Tree("path", [Token("IDENTIFIER", "some")])
                ])
              ])
            ,Tree("sep_by1", 
              [
              Tree("pattern_match",
                [
                Tree("pattern_maybe_constructor", 
                  [
                  Tree("path", [Token("IDENTIFIER", "things")])
                  ])
                ])
              ,Tree("pattern_match",
                  [
                  Tree("pattern_maybe_constructor", 
                    [
                    Tree("path", [Token("IDENTIFIER", "to")])
                    ])
                  ])
              ,Tree("pattern_match",
                  [
                  Tree("pattern_maybe_constructor", 
                    [
                    Tree("path", [Token("IDENTIFIER", "test")])
                    ])
                  ])
              ])
            ])
    )
    ] 
    parser = get_parser(start=rule_to_test)
    for (case,expected) in tests:
      parsed = parser(case)
      self.assertEqual(parsed, expected)


  def test_pattern_match_list(self):
    rule_to_test = "pattern_match_atom"
    tests  = [
    ("[]", Tree("pattern_empty_list",[]))
    ,("[a]", 
        Tree("pattern_list", 
            [
            Tree("sep_by1", 
              [
              Tree("pattern_match",
                [
                Tree("pattern_maybe_constructor", 
                  [
                  Tree("path", [Token("IDENTIFIER", "a")])
                  ])
                ])
              ])
            ])
    )
    ,("[a,b]",
        Tree("pattern_list", 
            [
            Tree("sep_by1", 
              [
              Tree("pattern_match",
                [
                Tree("pattern_maybe_constructor", 
                  [
                  Tree("path", [Token("IDENTIFIER", "a")])
                  ])
                ])
              ,Tree("pattern_match",
                [
                Tree("pattern_maybe_constructor", 
                  [
                  Tree("path", [Token("IDENTIFIER", "b")])
                  ])
                ])
              ])
            ])
    )
    ,("[some,things,to,test]",
        Tree("pattern_list", 
            [
            Tree("sep_by1", 
              [
              Tree("pattern_match",
                [
                Tree("pattern_maybe_constructor", 
                  [
                  Tree("path", [Token("IDENTIFIER", "some")])
                  ])
                ])
              ,Tree("pattern_match",
                [
                Tree("pattern_maybe_constructor", 
                  [
                  Tree("path", [Token("IDENTIFIER", "things")])
                  ])
                ])
              ,Tree("pattern_match",
                  [
                  Tree("pattern_maybe_constructor", 
                    [
                    Tree("path", [Token("IDENTIFIER", "to")])
                    ])
                  ])
              ,Tree("pattern_match",
                  [
                  Tree("pattern_maybe_constructor", 
                    [
                    Tree("path", [Token("IDENTIFIER", "test")])
                    ])
                  ])
              ])
            ])
    )
    ] 
    parser = get_parser(start=rule_to_test)
    for (case,expected) in tests:
      parsed = parser(case)
      self.assertEqual(parsed, expected)

if __name__ == '__main__':
 unittest.main()
