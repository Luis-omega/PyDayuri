import unittest 

from lark.exceptions import UnexpectedCharacters, UnexpectedToken

from ..load_grammar import get_parser

class Identifier(unittest.TestCase):
  def test_identifier_head_right(self):
    tests  = ["h","W","z"]
    rule_to_test = "test_identifier_head"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.data, rule_to_test)
      self.assertEqual(parsed.children, [case])

  def test_identifier_head_bad(self):
    tests = ["8","_","?","~"]
    rule_to_test = "test_identifier_head"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      with self.assertRaises(UnexpectedCharacters) as cm :
        parsed = parser(case)
        print(parsed.pretty())


  def test_identifier_right(self):
    tests  = ["weri_asdf8_sfd","DFEerw_we_ewr","ai837rr_"]
    rule_to_test = "test_identifier"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.data, rule_to_test)
      self.assertEqual(parsed.children, [case])

  def test_identifier_bad(self):
    tests  = ["8weri_asdf8_sfd","_DFEerw_we_ewr","?ai837rr_","\nasdf"]
    rule_to_test = "test_identifier"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      with self.assertRaises(UnexpectedCharacters) as cm :
        parsed = parser(case)
        print(parsed.pretty())

class Int(unittest.TestCase):
  def test_uint_head_right(self):
    tests  = ["1","8","3"]
    rule_to_test = "test_uint_head"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.data, rule_to_test)
      self.assertEqual(parsed.children, [case])

  def test_uint_bad(self):
    tests  = ["0","_"]
    rule_to_test = "test_uint_head"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      with self.assertRaises(UnexpectedCharacters) as cm :
        parsed = parser(case)
        print(parsed.pretty())

  def test_uint_body(self):
    tests  = ["_","0","3"]
    rule_to_test = "test_uint_body"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.data, rule_to_test)
      self.assertEqual(parsed.children, [case])


  def test_uint_right(self):
    tests  = ["1","80_0","30000_0_03_2___3"]
    rule_to_test = "test_uint"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.data, rule_to_test)
      self.assertEqual(parsed.children, [case])

  def test_uint_bad(self):
    tests  = ["034","_82763"]
    rule_to_test = "test_uint"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      with self.assertRaises(UnexpectedCharacters) as cm :
        parsed = parser(case)
        print(parsed.pretty())


class Keyword(unittest.TestCase):
  def test_keyword_right(self):
    tests  = ["import","as","with","module"]
    rule_to_test = "test_keywords"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.data, rule_to_test)
      self.assertEqual(parsed.children, [case])
  
  def test_keyword_bad(self):
    tests  = ["Asimport","aM","some"] 
    rule_to_test = "test_keywords"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      #parser must get a idenfier, so we "unexpect" a token instead of char
      with self.assertRaises(UnexpectedToken) as cm :
        parsed = parser(case)
        print(parsed.pretty())

  def test_keyword_over_identifier(self):
    tests  = ["import","as","with","module"]
    rule_to_test = "test_keywords_over_identifier"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.children[0].data, "test_keywords")
      self.assertEqual(parsed.children[0].children, [case])

    tests  = ["Asimport","aM","some"]
    rule_to_test = "test_keywords_over_identifier"
    parser = get_parser(start=rule_to_test)
    for case in tests:
      parsed = parser(case)
      self.assertEqual(parsed.children[0].data, "test_identifier")
      self.assertEqual(parsed.children[0].children, [case])
  


if __name__ == '__main__':
 unittest.main()
