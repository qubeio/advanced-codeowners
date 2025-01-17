# Advanced CodeOwners

A GitHub Action that enhances CodeOwners functionality with boolean expressions and advanced rules.

## Features

- Boolean expressions in CODEOWNERS files (AND, OR operations)
- Complex approval rules
- Automated PR merging based on correct approvals
- Support for team and individual approvals
- Automatic PR processing on review changes

## Usage

Add this action to your workflow:

```yaml
name: CodeOwners Check
on:
  pull_request_review:
    types: [submitted, edited, dismissed]

jobs:
  check-codeowners:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Required for merging PRs
      pull-requests: write  # Required for commenting on PRs
    steps:
      - uses: advanced-codeowners@v1
```

Note: The action automatically uses the `GITHUB_TOKEN` provided by GitHub Actions. No additional token configuration is needed.

## CODEOWNERS Syntax

The action supports standard CODEOWNERS syntax with additional boolean expressions:

```txt
# Standard rules work as normal
*.js    @org/javascript-team

# AND Rule: Both teams must approve
#@BOOL /api/* @org/backend-team AND @org/security-team
/api/*  @org/backend-team @org/security-team

# OR Rule: Either team can approve
#@BOOL /docs/* @org/docs OR @org/developers
/docs/* @org/docs @org/developers

# Complex Rules: Combine AND/OR
#@BOOL *.config.js (@org/devops OR @org/platform) AND @org/security-team
*.config.js @org/devops @org/platform @org/security-team
```

## How it Works

1. When a pull request review is submitted, edited, or dismissed, this action:
   - Reads your CODEOWNERS file
   - Parses any boolean expressions
   - Checks all required approvals
   - Automatically merges the PR if all requirements are met

2. The action will:
   - Merge the PR if all required approvals are present
   - Leave the PR open if approvals are missing
   - Add comments explaining what approvals are still needed

## Permissions

The GitHub token used must have:

- `contents: write` - For merging PRs

- `pull-requests: write` - For commenting on PRs

## Contributing

Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to contribute to this project.

## License

[MIT License](LICENSE)
