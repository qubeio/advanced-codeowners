# Contributing to Advanced CodeOwners

## Development

### Dev Environment setup

#### Option 1: Automated Setup (macOS/Linux)

```bash
task setup-dev
```

#### Option 2: Manual Setup

1. Install pyenv (if not already installed):

   ```bash
   # On macOS
   brew install pyenv

   # On Linux
   curl https://pyenv.run | bash
   ```

2. Install Python 3.13.0:

   ```bash
   pyenv install 3.13.0
   ```

3. Install uv:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. Clone and set up the project:

   ```bash
   git clone https://github.com/your-org/fo-advanced-codeowners.git
   cd fo-advanced-codeowners
   pyenv local 3.13.0  # This creates/updates .python-version
   ```

5. Create virtual environment and install dependencies:

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   uv pip install -e .
   ```

6. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

### Handling GitHub API Changes

If the integration tests fail with a message about API structure changes, this means the GitHub API response structure has been modified. To update the test fixtures:

1. Run the fixture update script:

   ```bash
   python tests/integration/update_fixtures.py
   ```

2. Review the changes in the fixture files:
   - `tests/integration/fixtures/pull_request.json.prev`
   - `tests/integration/fixtures/reviews.json.prev`

3. Update any corresponding mock structures in your tests to match the new API structure

4. Commit both the updated fixtures and mock changes in your PR
