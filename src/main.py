#!/usr/bin/env python3

import utils
from codeowners import CodeOwners
from github_api import GitHubAPI


def main():
    # Get GitHub Actions context
    required_vars = {
        "github_token": None,
        "github_repository": None,
        "github_event_path": None,
    }
    env_vars = utils.get_env(required_vars)

    # Initialize GitHub API client
    github_api = GitHubAPI(env_vars["github_token"])

    # Initialize CodeOwners
    codeowners = CodeOwners(github_api)

    # Get PR number from the event payload
    with open(env_vars["github_event_path"]) as f:
        import json

        event_data = json.load(f)
        pr_number = event_data["pull_request"]["number"]

    # Process the pull request with the context
    codeowners.process_pull_request(env_vars["github_repository"], pr_number)


if __name__ == "__main__":
    main()
