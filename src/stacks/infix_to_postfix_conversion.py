"""
https://en.wikipedia.org/wiki/Infix_notation
https://en.wikipedia.org/wiki/Reverse_Polish_notation
https://en.wikipedia.org/wiki/Shunting-yard_algorithm
"""

from typing import Literal

from src.stacks.balanced_parentheses import balanced_parentheses
from src.stacks.stack import Stack

PRECEDENCES: dict[str, int] = {
    "OR": 1,
    "AND": 2,
}
ASSOCIATIVITIES: dict[str, Literal["LR", "RL"]] = {
    "OR": "LR",
    "AND": "LR",
}


def precedence(token: str) -> int:
    """
    Return integer value representing an operator's precedence, or
    order of operation.
    https://en.wikipedia.org/wiki/Order_of_operations
    """
    return PRECEDENCES.get(token, -1)


def associativity(token: str) -> Literal["LR", "RL"]:
    """
    Return the associativity of the operator `token`.
    https://en.wikipedia.org/wiki/Operator_associativity
    """
    return ASSOCIATIVITIES.get(token, "LR")  # Default to left-to-right if not found


def infix_to_postfix(expression: list[str]) -> list[str]:
    """
    Convert an infix expression to a postfix expression.

    :param expression: A list of strings representing the infix expression.
                       Each string is either an operand (email address) or an operator ("AND" or "OR").
    :return: A list of strings representing the postfix expression.

    >>> infix_to_postfix(["user@example.com", "AND", "admin@example.com"])
    ['user@example.com', 'admin@example.com', 'AND']
    >>> infix_to_postfix(["a@b.com", "OR", "c@d.com", "AND", "e@f.com"])
    ['a@b.com', 'c@d.com', 'e@f.com', 'AND', 'OR']
    >>> infix_to_postfix(["(", "x@y.com", "AND", "p@q.com", ")", "OR", "m@n.com"])
    ['x@y.com', 'p@q.com', 'AND', 'm@n.com', 'OR']
    """
    if not balanced_parentheses(
        "".join(token for token in expression if token in "()")
    ):
        raise ValueError("Mismatched parentheses")
    stack: Stack[str] = Stack()
    postfix = []
    for token in expression:
        if token not in PRECEDENCES and token not in "()":
            postfix.append(token)  # It's an operand (email address)
        elif token == "(":
            stack.push(token)
        elif token == ")":
            while not stack.is_empty() and stack.peek() != "(":
                postfix.append(stack.pop())
            stack.pop()
        else:
            while True:
                if stack.is_empty():
                    stack.push(token)
                    break

                token_precedence = precedence(token)
                tos_precedence = precedence(stack.peek())

                if token_precedence > tos_precedence:
                    stack.push(token)
                    break
                if token_precedence < tos_precedence:
                    postfix.append(stack.pop())
                    continue
                # Precedences are equal
                if associativity(token) == "RL":
                    stack.push(token)
                    break
                postfix.append(stack.pop())

    while not stack.is_empty():
        postfix.append(stack.pop())
    return postfix


if __name__ == "__main__":
    from doctest import testmod

    testmod()

    expression = [
        "user@example.com",
        "AND",
        "(",
        "admin@example.com",
        "OR",
        "moderator@example.com",
        ")",
    ]

    print("Infix to Postfix Notation demonstration:\n")
    print("Infix notation:", expression)
    print("Postfix notation:", infix_to_postfix(expression))
