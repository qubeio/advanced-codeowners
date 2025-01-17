from typing import Any, Dict, List, Optional

from github import Auth, Github, PullRequest


class GitHubAPI:
    def __init__(self, token: str, owner: str):
        self.auth = Auth.Token(token)
        self.github = Github(auth=self.auth)
        self.owner = owner

    def close(self):
        self.github.close()

    def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequest:
        return self.github.get_repo(f"{owner}/{repo}").get_pull(number)

    def get_pull_request_approvers(self, repo: str, number: int) -> List[str]:
        """
        Retrieves a list of GitHub usernames who have approved a specific pull request.
        The usernames are returned as a list of strings, without the @ symbol.

        Args:
            repo (str): The name of the repository containing the pull request.
            number (int): The pull request number.

        Returns:
            list[str]: A list of GitHub usernames who have approved the pull request.
        """
        pr = self.get_pull_request(self.owner, repo, number)
        return [
            review.user.login
            for review in pr.get_reviews()
            if review.state == "APPROVED"
        ]

    def get_team_members(self, team_name: str) -> List[str]:
        """
        Retrieves a list of GitHub usernames who are members of a specific team.
        """
        org = self.github.get_organization(self.owner)
        # Try and get the team. If it doesn't exist, return an empty list and
        # log an error.
        try:
            team = org.get_team_by_slug(team_name)
            return [member.login for member in team.get_members()]
        except Exception as e:
            print(f"Team '{team_name}' does not exist: {str(e)}")
            raise Exception(f"Team '{team_name}' does not exist: {str(e)}")

    def get_raw_pull_request_data(
        self, owner: str, repo: str, number: int
    ) -> Dict[str, Any]:
        """Get raw pull request data for mock verification"""
        pr = self.get_pull_request(owner, repo, number)
        return pr._rawData

    def get_raw_review_data(self, owner: str, repo: str, number: int) -> List[dict]:
        """Get raw review data for mock verification"""
        pr = self.get_pull_request(owner, repo, number)
        return [review._rawData for review in pr.get_reviews()]

    def get_file_content(
        self, owner: str, repo: str, path: str, ref: Optional[str] = None
    ) -> str:
        """
        Gets the content of a file from the repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            path (str): Path to the file in the repository
            ref (str): The name of the commit/branch/tag. Defaults to None (uses default branch)

        Returns:
            str: Content of the file
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            file_content = repository.get_contents(path, ref=ref)
            if isinstance(file_content, list):
                raise ValueError(f"Path '{path}' points to a directory, not a file")
            return file_content.decoded_content.decode("utf-8")
        except Exception as e:
            raise Exception(f"Failed to get file content for {path}: {str(e)}")

    def get_pr_base_ref(self, owner: str, repo: str, number: int) -> str:
        """
        Gets the base branch reference of a pull request.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            number (int): Pull request number

        Returns:
            str: The base branch reference
        """
        pr = self.get_pull_request(owner, repo, number)
        return pr.base.ref
