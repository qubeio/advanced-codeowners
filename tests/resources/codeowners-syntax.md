# Warning

#There are some syntax rules for gitignore files that do not work in CODEOWNERS files:

# Escaping a pattern starting with # using \ so it is treated as a pattern and not a comment doesn't work
# Using ! to negate a pattern doesn't work
# Using [ ] to define a character range doesn't work

# A CODEOWNERS file uses a pattern that follows most of the same rules used in gitignore files. The pattern is followed by one or more GitHub usernames or team names using the standard @username or @org/team-name format. Users and teams must have explicit write access to the repository, even if the team's members already have access.

# GITIGNORE PATTERN SYNTAX
# PATTERN FORMAT

# A blank line matches no files, so it can serve as a separator for readability.

# A line starting with # serves as a comment. Put a backslash ("\") in front of the first hash for patterns that begin with a hash.

# Trailing spaces are ignored unless they are quoted with backslash ("\").

# The slash "/" is used as the directory separator. Separators may occur at the beginning, middle or end of the .gitignore search pattern.

# If there is a separator at the beginning or middle (or both) of the pattern, then the pattern is relative to the directory level of the particular .gitignore file itself. Otherwise the pattern may also match at any level below the .gitignore level.

# If there is a separator at the end of the pattern then the pattern will only match directories, otherwise the pattern can match both files and directories.

# For example, a pattern doc/frotz/ matches doc/frotz directory, but not a/doc/frotz directory; however frotz/ matches frotz and a/frotz that is a directory (all paths are relative from the .gitignore file).

# An asterisk "*" matches anything except a slash. The character "?" matches any one character except "/".

# Two consecutive asterisks ("**") in patterns matched against full pathname may have special meaning:

  # A leading "**" followed by a slash means match in all directories. For example,
  #  "**/foo" matches file or directory "foo" anywhere, the same as pattern "foo". "**/foo/bar"
  #  matches file or directory "bar" anywhere that is directly under directory "foo".

  # A trailing "/**" matches everything inside. For example, "abc/**" matches all files inside directory "abc", relative to the location of the .gitignore file, with infinite depth.

  # A slash followed by two consecutive asterisks then a slash matches zero or more directories. For example, "a/**/b" matches "a/b", "a/x/b", "a/x/y/b" and so on.

  # Other consecutive asterisks are considered regular asterisks and will match according to the previous rules.


# EXAMPLES AND SYNTAX
# This is a comment.
# Each line is a file pattern followed by one or more owners.

# These owners will be the default owners for everything in
# the repo. Unless a later match takes precedence,
# @global-owner1 and @global-owner2 will be requested for
# review when someone opens a pull request.
*       @global-owner1 @global-owner2

# Order is important; the last matching pattern takes the most
# precedence. When someone opens a pull request that only
# modifies JS files, only @js-owner and not the global
# owner(s) will be requested for a review.
*.js    @js-owner #This is an inline comment.

# You can also use email addresses if you prefer. They'll be
# used to look up users just like we do for commit author
# emails.
*.go docs@example.com

# Teams can be specified as code owners as well. Teams should
# be identified in the format @org/team-name. Teams must have
# explicit write access to the repository. In this example,
# the octocats team in the octo-org organization owns all .txt files.
*.txt @octo-org/octocats

# In this example, @doctocat owns any files in the build/logs
# directory at the root of the repository and any of its
# subdirectories.
/build/logs/ @doctocat

# The `docs/*` pattern will match files like
# `docs/getting-started.md` but not further nested files like
# `docs/build-app/troubleshooting.md`.
docs/* docs@example.com

# In this example, @octocat owns any file in an apps directory
# anywhere in your repository.
apps/ @octocat

# In this example, @doctocat owns any file in the `/docs`
# directory in the root of your repository and any of its
# subdirectories.
/docs/ @doctocat

# In this example, any change inside the `/scripts` directory
# will require approval from @doctocat or @octocat.
/scripts/ @doctocat @octocat

# In this example, @octocat owns any file in a `/logs` directory such as
# `/build/logs`, `/scripts/logs`, and `/deeply/nested/logs`. Any changes
# in a `/logs` directory will require approval from @octocat.
**/logs @octocat

# In this example, @octocat owns any file in the `/apps`
# directory in the root of your repository except for the `/apps/github`
# subdirectory, as its owners are left empty. Without an owner, changes
# to `apps/github` can be made with the approval of any user who has
# write access to the repository.
/apps/ @octocat
/apps/github

# In this example, @octocat owns any file in the `/apps`
# directory in the root of your repository except for the `/apps/github`
# subdirectory, as this subdirectory has its own owner @doctocat
/apps/ @octocat
/apps/github @doctocat
