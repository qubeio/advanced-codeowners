import unittest
from unittest.mock import Mock, patch

from src.github_api import GitHubAPI


class TestGitHubAPI(unittest.TestCase):

    @patch("src.github_api.Github")
    def test_get_pull_request_approvers(self, mock_github):
        # Setup
        mock_repo = Mock()
        mock_pr = Mock()
        mock_review1 = Mock(user=Mock(login="user1"), state="APPROVED")
        mock_review2 = Mock(user=Mock(login="user2"), state="COMMENTED")
        mock_review3 = Mock(user=Mock(login="user3"), state="APPROVED")

        mock_github.return_value.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_reviews.return_value = [mock_review1, mock_review2, mock_review3]

        # Create GitHubAPI instance
        api = GitHubAPI(token="fake_token", owner="fake_owner")

        # Call the method
        approvers = api.get_pull_request_approvers("fake_repo", 123)

        # Assert
        self.assertEqual(approvers, ["user1", "user3"])
        mock_github.return_value.get_repo.assert_called_once_with(
            "fake_owner/fake_repo"
        )
        mock_repo.get_pull.assert_called_once_with(123)


if __name__ == "__main__":
    unittest.main()
