import unittest

from src.stacks.infix_to_postfix_conversion import infix_to_postfix


class TestInfixToPostfixConversion(unittest.TestCase):

    def test_simple_and_expression(self):
        infix = ["user@example.com", "AND", "admin@example.com"]
        expected = ["user@example.com", "admin@example.com", "AND"]
        self.assertEqual(infix_to_postfix(infix), expected)

    def test_complex_expression_with_parentheses(self):
        infix = ["(", "x@y.com", "AND", "p@q.com", ")", "OR", "m@n.com"]
        expected = ["x@y.com", "p@q.com", "AND", "m@n.com", "OR"]
        self.assertEqual(infix_to_postfix(infix), expected)


if __name__ == "__main__":
    unittest.main()
