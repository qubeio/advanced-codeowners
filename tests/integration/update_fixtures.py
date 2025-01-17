import shutil
from pathlib import Path

from test_github_api_integration import TestGitHubAPIMockVerification


def update_fixture_files():
    """Update the .prev fixture files with current API responses"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    # Run the test to generate new fixture files
    test = TestGitHubAPIMockVerification("test_verify_mock_structures")
    test.setUpClass()
    test.test_verify_mock_structures()

    # Copy current files to .prev files
    for fixture in ["pull_request.json", "reviews.json"]:
        current = fixtures_dir / fixture
        prev = fixtures_dir / f"{fixture}.prev"
        if current.exists():
            shutil.copy2(current, prev)
            print(f"Updated {prev}")


if __name__ == "__main__":
    update_fixture_files()
