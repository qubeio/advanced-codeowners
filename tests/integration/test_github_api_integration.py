import json
import os
import unittest
from pathlib import Path

from dotenv import load_dotenv

from src.github_api import GitHubAPI


class TestGitHubAPIIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Load environment variables from .env file if this is not a CI environment
        if not os.getenv("CI"):
            load_dotenv()

        # Get GitHub token from environment variable
        cls.token = os.getenv("GITHUB_TOKEN")
        if not cls.token:
            raise unittest.SkipTest("GITHUB_TOKEN environment variable is not set")

        # Set up test parameters
        cls.owner = "qubeio"  # Example: use a public GitHub account
        cls.repo = "PlatformArchitecture-docs"  # Example: use a public repository
        cls.pr_number = 34  # Example: use a known PR number

        cls.api = GitHubAPI(token=cls.token, owner=cls.owner)

    def test_get_pull_request_approvers(self):
        approvers = self.api.get_pull_request_approvers(self.repo, self.pr_number)

        # Basic assertions
        self.assertIsInstance(approvers, list)
        for approver in approvers:
            self.assertIsInstance(approver, str)

    def test_get_team_members(self):
        # Use a known team from your organization
        team_name = "FusionOperate-Architect"  # Replace with a real team name

        # Get team members
        members = self.api.get_team_members(team_name)

        # Basic structure assertions
        self.assertIsInstance(members, list)
        self.assertGreater(len(members), 0, "Team should have at least one member")

        # Verify each member is a string (username)
        for member in members:
            self.assertIsInstance(member, str)
            self.assertGreater(len(member), 0, "Username should not be empty")

    def test_get_team_members_nonexistent_team(self):
        # Test with a team that doesn't exist
        with self.assertRaises(Exception):  # Replace with specific exception if known
            self.api.get_team_members("non-existent-team-name")


class TestGitHubAPIMockVerification(unittest.TestCase):
    """Tests to verify that our mock structures match the real API"""

    @classmethod
    def setUpClass(cls):
        # Same setup as TestGitHubAPIIntegration
        if not os.getenv("CI"):
            load_dotenv()

        cls.token = os.getenv("GITHUB_TOKEN")
        if not cls.token:
            raise unittest.SkipTest("GITHUB_TOKEN environment variable is not set")

        cls.owner = "octocat"
        cls.repo = "Hello-World"
        cls.pr_number = 1
        cls.api = GitHubAPI(token=cls.token, owner=cls.owner)

        # Get fixtures directory path
        cls.fixtures_dir = Path(__file__).parent / "fixtures"
        if not cls.fixtures_dir.exists():
            raise RuntimeError(f"Fixtures directory {cls.fixtures_dir} does not exist")

    def _save_current_fixtures(self, pr_data, review_data):
        """Save current API responses as fixtures"""
        with open(self.fixtures_dir / "pull_request.json", "w") as f:
            json.dump(pr_data, f, indent=2)
        with open(self.fixtures_dir / "reviews.json", "w") as f:
            json.dump(review_data, f, indent=2)

    def _load_previous_fixtures(self):
        """Load previous API responses from fixtures"""
        try:
            with open(self.fixtures_dir / "pull_request.json.prev", "r") as f:
                pr_data = json.load(f)
            with open(self.fixtures_dir / "reviews.json.prev", "r") as f:
                review_data = json.load(f)
            return pr_data, review_data
        except FileNotFoundError:
            return None, None

    def test_verify_mock_structures(self):
        # Get real data from API
        pr_data = self.api.get_raw_pull_request_data(
            self.owner, self.repo, self.pr_number
        )
        review_data = self.api.get_raw_review_data(
            self.owner, self.repo, self.pr_number
        )

        # Save current API responses as fixtures
        self._save_current_fixtures(pr_data, review_data)

        # Load and compare with previous fixtures
        prev_pr_data, prev_review_data = self._load_previous_fixtures()
        if prev_pr_data and prev_review_data:
            self.assertEqual(
                set(self._get_all_keys(pr_data)),
                set(self._get_all_keys(prev_pr_data)),
                "PR API structure has changed! Update your mocks by running update_fixtures.py",
            )
            if review_data and prev_review_data:
                self.assertEqual(
                    set(self._get_all_keys(review_data[0])),
                    set(self._get_all_keys(prev_review_data[0])),
                    "Review API structure has changed! Update your mocks by running update_fixtures.py",
                )

    def _get_all_keys(self, obj, prefix="") -> set:
        """Recursively get all keys in a nested dict/list structure"""
        keys = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.add(f"{prefix}{k}")
                keys.update(self._get_all_keys(v, f"{prefix}{k}."))
        elif isinstance(obj, list) and obj and isinstance(obj[0], (dict, list)):
            keys.update(self._get_all_keys(obj[0], prefix))
        return keys


if __name__ == "__main__":
    unittest.main()
