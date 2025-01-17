import os
import unittest
from unittest.mock import Mock, call

from dotenv import load_dotenv

from src.codeowners import CodeOwners


class TestCodeOwners(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_dotenv()

    def test_parse_codeowners_file(self):
        # Mock GitHub API
        mock_github_api = Mock()
        mock_github_api.owner = "test-org"
        mock_github_api.get_pr_base_ref.return_value = "main"

        # Mock the CODEOWNERS file content. Excuse the formatting.
        mock_content = """
# Standard rule
*.js    @org/javascript-team

# Boolean rules
#@BOOL /folder1 (@org/reviewer-group2 OR @org/reviewer-group1 OR @org/reviewer-group3) AND @org/reviewer-group4
#@BOOL file1 @org/reviewer-group2 AND @org/reviewer-group1
#@BOOL **/folder3 @org/reviewer-group3 AND @org/reviewer-group4
"""
        mock_github_api.get_file_content.return_value = mock_content

        codeowners = CodeOwners(mock_github_api, os.environ)
        rules = codeowners.parse_codeowners_file("test-repo", 123)

        # Test that rules were extracted correctly
        expected_rules = {
            "/folder1": (
                "(@org/reviewer-group2 OR @org/reviewer-group1 OR "
                "@org/reviewer-group3) AND @org/reviewer-group4"
            ),
            "file1": "@org/reviewer-group2 AND @org/reviewer-group1",
            "**/folder3": "@org/reviewer-group3 AND @org/reviewer-group4",
        }

        # Verify rules dictionary matches expected structure
        self.assertEqual(len(rules), len(expected_rules))
        for path, rule in expected_rules.items():
            self.assertIn(path, rules.keys())
            self.assertIsInstance(rules[path], str)
            self.assertEqual(rules[path].strip(), rule.strip())

        # Verify mock calls
        mock_github_api.get_pr_base_ref.assert_called_once_with(
            "test-org", "test-repo", 123
        )
        mock_github_api.get_file_content.assert_called_once_with(
            "test-org", "test-repo", ".github/CODEOWNERS", ref="main"
        )

        # Test with empty file
        mock_github_api.get_file_content.return_value = ""
        empty_rules = codeowners.parse_codeowners_file("test-repo", 123)
        self.assertEqual(empty_rules, {})

        # Test with file containing no boolean rules
        mock_github_api.get_file_content.return_value = "* @org/team1\n/path @org/team2"
        no_bool_rules = codeowners.parse_codeowners_file("test-repo", 123)
        self.assertEqual(no_bool_rules, {})

    def test_parse_boolean_expression(self):
        codeowners = CodeOwners(None, os.environ)

        # Test single reviewer
        tokens = codeowners.tokenize_boolean_expression("@reviewer1")
        self.assertEqual(tokens, ["@reviewer1"])

        # Test AND operation
        tokens = codeowners.tokenize_boolean_expression("@reviewer1 AND @reviewer2")
        self.assertEqual(tokens, ["@reviewer1", "AND", "@reviewer2"])

        # Test OR operation
        tokens = codeowners.tokenize_boolean_expression("@reviewer1 OR @reviewer2")
        self.assertEqual(tokens, ["@reviewer1", "OR", "@reviewer2"])

        # Test parentheses
        tokens = codeowners.tokenize_boolean_expression("(@reviewer1)")
        self.assertEqual(tokens, ["(", "@reviewer1", ")"])

        # Test complex expression
        expression = "(@reviewer1 OR @reviewer2) AND @reviewer3"
        expected = ["(", "@reviewer1", "OR", "@reviewer2", ")", "AND", "@reviewer3"]
        tokens = codeowners.tokenize_boolean_expression(expression)
        self.assertEqual(tokens, expected)

        # Test empty expression
        tokens = codeowners.tokenize_boolean_expression("")
        self.assertEqual(tokens, [])

        # Test space handling
        tokens = codeowners.tokenize_boolean_expression(
            "  @reviewer1    AND   @reviewer2  "
        )
        self.assertEqual(tokens, ["@reviewer1", "AND", "@reviewer2"])

    def test_tokenize_boolean_expression_corner_cases(self):
        codeowners = CodeOwners(None, os.environ)

        # Test invalid characters
        tokens = codeowners.tokenize_boolean_expression("@reviewer1 & @reviewer2")
        self.assertEqual(tokens, ["@reviewer1", "@reviewer2"])

        # Test nested parentheses
        tokens = codeowners.tokenize_boolean_expression("((@reviewer1 AND @reviewer2))")
        self.assertEqual(
            tokens, ["(", "(", "@reviewer1", "AND", "@reviewer2", ")", ")"]
        )

        # Test multiple spaces
        tokens = codeowners.tokenize_boolean_expression(
            "@reviewer1  AND     @reviewer2"
        )
        self.assertEqual(tokens, ["@reviewer1", "AND", "@reviewer2"])

        # Test complex organization/team names with multiple hyphens
        tokens = codeowners.tokenize_boolean_expression(
            "@qubeio/FusionOperate-Architect AND @qubeio/DevEng-Architect"
        )
        self.assertEqual(
            tokens,
            [
                "@qubeio/FusionOperate-Architect",
                "AND",
                "@qubeio/DevEng-Architect",
            ],
        )

        # Test mixed complex and simple team names
        tokens = codeowners.tokenize_boolean_expression(
            "(@org/simple-team OR @qubeio/Complex-Team-Name)"
        )
        self.assertEqual(
            tokens,
            [
                "(",
                "@org/simple-team",
                "OR",
                "@qubeio/Complex-Team-Name",
                ")",
            ],
        )

        # Test group names with underscores and hyphens
        tokens = codeowners.tokenize_boolean_expression(
            "@org-name/team_name-1 AND @org-name/other-team_2"
        )
        self.assertEqual(
            tokens, ["@org-name/team_name-1", "AND", "@org-name/other-team_2"]
        )

    def test_evaluate_boolean_expression(self):
        # Mock the GitHubAPI class
        mock_github_api = Mock()
        mock_github_api.get_team_members.side_effect = lambda team_name: {
            "team1": ["user1", "user2"],
            "team2": ["user3", "user4"],
            "team3": ["user5", "user6"],
        }[team_name]

        codeowners = CodeOwners(mock_github_api, os.environ)

        # Test cases with group-based reviewers
        reviewers = {"user1", "user3", "user5"}  # One member from each team

        # Test single group
        tokens = ["@org/team1"]
        self.assertTrue(codeowners.evaluate_boolean_expression(tokens, reviewers))

        # Test AND operation with groups
        tokens = ["@org/team1", "@org/team2", "AND"]
        self.assertTrue(codeowners.evaluate_boolean_expression(tokens, reviewers))

        # Test OR operation with groups
        tokens = ["@org/team1", "@org/team3", "OR"]
        self.assertTrue(codeowners.evaluate_boolean_expression(tokens, reviewers))

        # Test complex expression: (@org/team1 OR @org/team2) AND @org/team3
        tokens = ["@org/team1", "@org/team2", "OR", "@org/team3", "AND"]
        self.assertTrue(codeowners.evaluate_boolean_expression(tokens, reviewers))

        # TEST FAILING CASES

        # Test single group with no matching reviewers
        reviewers_no_match = {"user7", "user8"}
        tokens = ["@org/team1"]
        self.assertFalse(
            codeowners.evaluate_boolean_expression(tokens, reviewers_no_match)
        )

        # Test AND operation where one group fails
        reviewers_partial = {"user1", "user7"}  # Only matches team1
        tokens = ["@org/team1", "@org/team2", "AND"]
        self.assertFalse(
            codeowners.evaluate_boolean_expression(tokens, reviewers_partial)
        )

        # Verify mock calls
        mock_github_api.get_team_members.assert_has_calls(
            [call("team1"), call("team2"), call("team3")], any_order=True
        )

    def test_evaluate_changed_files(self):
        # Mock the GitHubAPI class
        mock_github_api = Mock()
        # Set up the mock to return specific team members when get_team_members is called
        mock_github_api.get_team_members.side_effect = lambda team_name: {
            "reviewer-group1": ["user1", "user2"],
            "reviewer-group2": ["user3", "user4"],
            "reviewer-group3": ["user5", "user6"],
            "reviewer-group4": ["user7", "user8"],
        }[team_name]

        codeowners = CodeOwners(mock_github_api, os.environ)

        # Setup test data with various path patterns
        changed_files = [
            "folder1/some_file.txt",
            "folder1/subfolder/file.js",
            "file1",
            "folder2/test.py",
            "deep/nested/folder3/file.js",
            "docs/README.md",
        ]

        rules = {
            "/folder1": (
                "(@org/reviewer-group2 OR @org/reviewer-group1 OR "
                "@org/reviewer-group3) AND @org/reviewer-group4"
            ),
            "file1": "@org/reviewer-group2 AND @org/reviewer-group1",
            "**/folder3": "@org/reviewer-group3 AND @org/reviewer-group4",
            "docs/": "@org/reviewer-group1",
        }

        # Test case 1: No reviewers
        reviewers = set()
        results = codeowners.evaluate_changed_files(changed_files, rules, reviewers)

        # Verify the mock was called with the correct team names
        mock_github_api.get_team_members.assert_any_call("reviewer-group1")
        mock_github_api.get_team_members.assert_any_call("reviewer-group2")
        mock_github_api.get_team_members.assert_any_call("reviewer-group3")
        mock_github_api.get_team_members.assert_any_call("reviewer-group4")

        # Verify folder1 matches (both direct and nested files)
        folder1_direct = results["folder1/some_file.txt"]
        folder1_nested = results["folder1/subfolder/file.js"]
        self.assertEqual(len(folder1_direct), 1)
        self.assertEqual(len(folder1_nested), 1)
        self.assertEqual(folder1_direct[0]["path"], "/folder1")
        self.assertEqual(folder1_nested[0]["path"], "/folder1")
        self.assertFalse(folder1_direct[0]["satisfied"])
        self.assertFalse(folder1_nested[0]["satisfied"])

        # Additional test for file vs directory matching
        rules_with_file_pattern = {
            # This should match "folder1" file and "folder1/something"
            "folder1": "@org/reviewer-group1",
            # This should match any file under folder1/
            "folder1/": "@org/reviewer-group2",
        }

        test_files = [
            "folder1",  # Should match "folder1" and not"folder1/" pattern
            "folder1/file.txt",  # Should match "folder1/" pattern
            "folder1/deep/file",  # Should match "folder1/" pattern
        ]

        results = codeowners.evaluate_changed_files(
            test_files, rules_with_file_pattern, reviewers
        )

        # Verify file pattern match
        self.assertEqual(len(results["folder1"]), 1)
        self.assertEqual(results["folder1"][0]["path"], "folder1")

        # Verify directory pattern matches
        self.assertEqual(len(results["folder1/file.txt"]), 2)
        self.assertEqual(len(results["folder1/deep/file"]), 2)
        self.assertEqual(results["folder1/file.txt"][0]["path"], "folder1")
        self.assertEqual(results["folder1/deep/file"][0]["path"], "folder1")

        # Verify directory pattern matche ordering
        self.assertEqual(results["folder1/file.txt"][1]["path"], "folder1/")
        self.assertEqual(results["folder1/deep/file"][1]["path"], "folder1/")

        # Verify rules not satisfied
        self.assertFalse(results["folder1/file.txt"][0]["satisfied"])
        self.assertFalse(results["folder1/deep/file"][0]["satisfied"])
        self.assertFalse(results["folder1"][0]["satisfied"])

        # Test case 2: Some required reviewers present
        reviewers = {"user1", "user2"}
        results = codeowners.evaluate_changed_files(changed_files, rules, reviewers)

        # Check file1 results (exact match)
        file1_results = results["file1"]
        self.assertFalse(file1_results[0]["satisfied"])

        # Check docs folder match
        docs_results = results["docs/README.md"]
        self.assertEqual(len(docs_results), 1)
        self.assertEqual(docs_results[0]["path"], "docs/")
        self.assertTrue(docs_results[0]["satisfied"])

        # Test case 3: All required reviewers present
        reviewers = {
            "user1",
            "user2",
            "user3",
            "user4",
            "user5",
            "user6",
            "user7",
            "user8",
        }
        results = codeowners.evaluate_changed_files(changed_files, rules, reviewers)

        # Check folder3 results (glob pattern match)
        folder3_results = results["deep/nested/folder3/file.js"]
        self.assertEqual(len(folder3_results), 1)
        self.assertEqual(folder3_results[0]["path"], "**/folder3")
        self.assertTrue(folder3_results[0]["satisfied"])

    def test_matches_pattern(self):
        codeowners = CodeOwners(None, os.environ)

        # Test exact file matches
        self.assertTrue(codeowners.matches_pattern("file.txt", "file.txt"))
        self.assertTrue(codeowners.matches_pattern("path/to/file.txt", "file.txt"))
        self.assertFalse(codeowners.matches_pattern("file.txt2", "file.txt"))

        # Test directory matches (trailing slash)
        self.assertTrue(codeowners.matches_pattern("docs/file.md", "docs/"))
        self.assertTrue(codeowners.matches_pattern("docs/subfolder/file.md", "docs/"))
        self.assertFalse(
            codeowners.matches_pattern("other/docs/mydocs/file.md", "docs/mydocs")
        )

        # Test anchored paths (leading slash)
        self.assertTrue(codeowners.matches_pattern("docs/file.md", "/docs/file.md"))
        self.assertFalse(
            codeowners.matches_pattern("src/docs/file.md", "/docs/file.md")
        )

        # Test wildcard patterns
        self.assertTrue(codeowners.matches_pattern("file.js", "*.js"))
        self.assertTrue(codeowners.matches_pattern("path/to/file.js", "*.js"))
        self.assertTrue(
            codeowners.matches_pattern("docs/mydocs/file.md", "docs/*/file.md")
        )
        self.assertTrue(
            codeowners.matches_pattern("docs/mydocs/file.md", "docs/*/*.md")
        )
        self.assertFalse(
            codeowners.matches_pattern("docs/mydocs/other/file.md", "docs/*/file.md")
        )
        self.assertFalse(codeowners.matches_pattern("file.jsx", "*.js"))

        # Test directory wildcards (**)
        self.assertTrue(
            codeowners.matches_pattern("any/path/to/docs/file.md", "**/docs/file.md")
        )
        self.assertTrue(codeowners.matches_pattern("docs/file.md", "**/docs/file.md"))
        self.assertFalse(codeowners.matches_pattern("docs/other.md", "**/docs/file.md"))

        # Test question mark pattern
        self.assertTrue(codeowners.matches_pattern("file1.js", "file?.js"))
        self.assertTrue(codeowners.matches_pattern("filea.js", "file?.js"))
        self.assertFalse(codeowners.matches_pattern("file10.js", "file?.js"))

        # Test combined patterns
        self.assertTrue(
            codeowners.matches_pattern("src/js/feature/index.ts", "**/js/**/*.ts")
        )
        self.assertTrue(
            codeowners.matches_pattern(
                "deep/path/js/other/path/file.ts", "**/js/**/*.ts"
            )
        )
        self.assertFalse(
            codeowners.matches_pattern("src/js/feature/index.tsx", "**/js/**/*.ts")
        )

        # Test directory vs file patterns
        self.assertTrue(codeowners.matches_pattern("docs/README.md", "docs/"))
        self.assertFalse(codeowners.matches_pattern("docs", "docs/"))
        self.assertTrue(codeowners.matches_pattern("docs", "docs"))
        self.assertTrue(codeowners.matches_pattern("docs/file.txt", "docs"))
        self.assertTrue(codeowners.matches_pattern("somedir/docs/file.txt", "docs"))

        # Test dot files and directories
        self.assertTrue(
            codeowners.matches_pattern(
                ".github/workflows/test.yml", ".github/workflows/*.yml"
            )
        )
        self.assertTrue(codeowners.matches_pattern(".env", ".env"))
        self.assertFalse(codeowners.matches_pattern(".env.local", ".env"))

        # Test complex nested patterns
        self.assertTrue(
            codeowners.matches_pattern(
                "apps/web/src/components/Button.tsx", "apps/**/components/*.tsx"
            )
        )
        self.assertTrue(
            codeowners.matches_pattern(
                "apps/mobile/src/components/Button.tsx", "apps/**/components/*.tsx"
            )
        )
        self.assertTrue(
            codeowners.matches_pattern(
                "apps/web/components/Button.tsx", "apps/*/components/*.tsx"
            )
        )
        self.assertFalse(
            codeowners.matches_pattern(
                "libs/components/Button.tsx", "apps/**/components/*.tsx"
            )
        )
