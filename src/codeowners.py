import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Union

import pathspec

from src.github_api import GitHubAPI
from src.stacks.infix_to_postfix_conversion import infix_to_postfix
from src.stacks.stack import Stack


class CodeOwners:
    def __init__(self, github_api: GitHubAPI, environ_vars: Dict[str, str]) -> None:
        self.github_api = github_api
        self.github_environ = environ_vars.get(
            "GITHUB_ENVIRONMENT", ""
        )  # Add default empty string
        self.repo = environ_vars.get("GITHUB_REPOSITORY", "").split("/")[-1]

    def process_pull_request(
        self, pr_number: int
    ) -> tuple[bool, Dict[str, List[Dict[str, Union[str, bool]]]]]:
        """
        Process a pull request and verify if it meets the CODEOWNERS boolean rules.

        Args:
            pr_number (int): The pull request number to process

        Returns:
            tuple: (bool, dict) - Success status and detailed results per file
        """

        # Get current reviewers who have approved
        reviewers = set(
            self.github_api.get_pull_request_approvers(self.repo, pr_number)
        )

        # Get the PR object to check changed files
        pr = self.github_api.get_pull_request(
            self.github_api.owner, self.repo, pr_number
        )
        changed_files = [file.filename for file in pr.get_files()]  # type: ignore

        # Parse CODEOWNERS file
        rules = self.parse_codeowners_file(self.repo, pr_number)

        results = self.evaluate_changed_files(changed_files, rules, reviewers)
        all_satisfied = all(
            any(result["satisfied"] for result in file_results)
            for file_results in results.values()
        )

        # If all_satisfied is False, we need to get the reviewers who have not satisfied the rules
        # and print out the rules that are not satisfied. This is also a GitHub
        # Action so we should fail the workflow if not all rules are satisfied.
        if not all_satisfied:
            print("::group::CodeOwners Validation Failed")
            print("::error::Pull request does not have required approvals")
            print("\nThe following rules are not satisfied:")
            for file, file_results in results.items():
                for result in file_results:
                    if not result["satisfied"]:
                        print(f"::error file={file}::{result['rule']}")
            print("::endgroup::")
            # Create a custom exception with both the message and results
            raise Exception("Pull request does not have required approvals", results)

        return all_satisfied, dict(results)

    def matches_pattern(self, filepath: str, pattern: str) -> bool:
        """
        Match a CODEOWNERS pattern against a file path.
        Returns True if the pattern matches the filepath, False otherwise.

        Args:
            filepath (str): The file path to match against the pattern.
            pattern (str): The pattern to match against the file path.

        Returns:
            bool: True if the pattern matches the filepath, False otherwise.
        """
        spec = pathspec.gitignore.GitIgnoreSpec.from_lines([pattern])
        return spec.match_file(filepath)

    def evaluate_changed_files(
        self, changed_files: List[str], rules: Dict[str, str], reviewers: Set[str]
    ) -> Dict[str, List[Dict[str, Union[str, bool]]]]:
        """
        Evaluate changed files against CODEOWNERS rules.
        Invalid rules are treated as automatically satisfied.

        Args:
            changed_files (list[str]): A list of file paths that have changed.
            rules (dict[str, str]): A dictionary of CODEOWNERS rules.
            reviewers (set[str]): A set of reviewers' usernames or groups.

        Returns:
            dict: A dictionary where keys are file paths and values are lists of dictionaries
                containing the path (str), rule (str), and satisfied (bool) status.
        """
        results: defaultdict[str, List[Dict[str, Union[str, bool]]]] = defaultdict(list)
        for file in changed_files:
            for pattern, rule in rules.items():
                if self.matches_pattern(file, pattern):
                    tokens = self.tokenize_boolean_expression(rule)
                    if tokens is None:
                        # Invalid syntax - treat as automatically satisfied
                        results[file].append(
                            {"path": pattern, "rule": rule, "satisfied": True}
                        )
                        continue

                    postfix_tokens = infix_to_postfix(tokens)
                    satisfied = self.evaluate_boolean_expression(
                        postfix_tokens, reviewers
                    )
                    results[file].append(
                        {"path": pattern, "rule": rule, "satisfied": satisfied}
                    )

        return dict(results)

    def parse_codeowners_file(self, repo: str, pr_number: int) -> Dict[str, str]:
        """
        Parses a CODEOWNERS file from the base branch of the PR.

        Args:
            repo (str): Repository name
            pr_number (int): Pull request number

        Returns:
            Dict[str, str]: A dictionary where keys are file paths and values are boolean rules.
        """
        rules = {}
        try:
            # Get the base branch of the PR
            base_ref = self.github_api.get_pr_base_ref(
                self.github_api.owner, repo, pr_number
            )

            # Get the content of CODEOWNERS file from the base branch
            content = self.github_api.get_file_content(
                self.github_api.owner, repo, ".github/CODEOWNERS", ref=base_ref
            )

            # Parse the content line by line
            for line in content.splitlines():
                if line.startswith("#@BOOL"):
                    parts = line.split(maxsplit=2)
                    path = parts[1]
                    bool_rule = parts[2].strip()
                    rules[path] = bool_rule

        except Exception as e:
            print(f"Error reading CODEOWNERS file: {e}")
            raise

        return rules

    def tokenize_boolean_expression(self, expression: str) -> Optional[List[str]]:
        """
        Parses a boolean expression and returns a list of tokens.
        Returns None if the expression has syntax errors.

        Args:
            expression (str): The boolean expression to parse.

        Returns:
            list[str] or None: A list of tokens if valid, None if syntax is invalid.
                Valid tokens include 'AND', 'OR', '(', ')', and '@username' or '@org/team'.
        """
        try:
            # Count parentheses to ensure they're balanced
            if expression.count("(") != expression.count(")"):
                print(
                    f"Warning: Malformed boolean expression (unbalanced parentheses): {expression}"
                )
                return None

            # Check for valid operators and tokens
            tokens = re.findall(r"\(|\)|AND|OR|@[\w-]+(?:/[\w-]+)?", expression)

            # Basic syntax validation
            for i, token in enumerate(tokens):
                if token not in ("AND", "OR", "(", ")") and not token.startswith("@"):
                    print(f"Warning: Invalid token in expression: {token}")
                    return None

                # Check for consecutive operators
                if i > 0 and token in ("AND", "OR") and tokens[i - 1] in ("AND", "OR"):
                    print(f"Warning: Consecutive operators in expression: {expression}")
                    return None

            return tokens
        except Exception as e:
            print(
                f"Warning: Failed to parse boolean expression: {expression}. Error: {str(e)}"
            )
            return None

    def evaluate_boolean_expression(
        self, tokens: List[str], reviewers: Set[str]
    ) -> bool:
        """
        Evaluates a boolean expression given as a list of tokens in postfix notation.
        For more information on postfix notation, see:
        https://en.wikipedia.org/wiki/Reverse_Polish_notation

        Args:
            tokens (list): A list of tokens representing the boolean expression in postfix notation.
            reviewers (set): A set of reviewers' usernames or groups.

        Returns:
            bool: The result of the boolean expression evaluation.
        """

        stack: Stack[bool] = Stack()
        for token in tokens:
            if token == "AND":
                right_operand = stack.pop()
                left_operand = stack.pop()
                stack.push(left_operand and right_operand)
            elif token == "OR":
                right_operand = stack.pop()
                left_operand = stack.pop()
                stack.push(left_operand or right_operand)
            elif token.startswith("@"):
                if "/" in token:
                    team_name = token.split("/")[-1]
                    try:
                        team_members = self.github_api.get_team_members(team_name)
                        stack.push(any(member in reviewers for member in team_members))
                    except Exception:
                        print(
                            f"Warning: Team '{team_name}' not found. Treating as empty group."
                        )
                        stack.push(False)  # Empty group means no approvals
                else:
                    stack.push(token in reviewers)
        return stack.pop()
