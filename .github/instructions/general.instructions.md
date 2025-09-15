---
applyTo: '**'
---

# General Instructions

## Temp folder and temp files
**When in agent mode**, creating intermediate or temporary test files, always create them in the `./temp` folder. If it doesn't exist create teh `temp` folder and and make sure it's ignored by git. If it's not already mentioned in the `.gitignore` file in the repo root, then add a `./temp/.gitignore` file containing only an asterisk (`*`).


## Branch names and the process we use
We do not use pull requests.

We generally use the GitHub CLI extension [gh-tt](https://github.com/thetechcollective/gh-tt) to manage our issues and branches. Most impotantly it supports `workon`, `wrapup` and `deliver`. 

```
usage: gh tt workon [-i ISSUE | -t TITLE]

options:
  -i ISSUE              Issue number for an existing issue
  -t TITLE              Title for the new issue, will create a new issue
```

This will create a new branch named with the issue number as prefix (e.g. `321-Update_summary_instructions`) and switch to that branch. The branch name is part of the zsh prompt in the @terminal, and can be directly accessed; The `$PS1` is set up to show the branch name too (e.g. `vscode ➜ /workspaces/gh-tt (321-Update_summary_instructions) $` means that we're working on issue 321). 

IMPORTANT: When asked to annotate issue summaries or perform other issue-related tasks, ALWAYS extract the issue number directly from the terminal prompt (the number before the hyphen in the branch name shown in parentheses). DO NOT run additional git commands like `git branch --show-current` to determine this information.
```

This update explicitly instructs to extract the issue number directly from the terminal prompt and specifically advises against running additional git commands for this purpose.

```
usage: gh tt wrapup [message]

positional arguments:
  message               Message for the commit 
```

This will stage all changes, commit them with the provided message and push the branch to origin. This will trigger the `.github/workflows/wrapup.yml` workflow which will run unittests and linting. `wrapup` is also subject to pre-commit hooks, which roughly mimic the `wrapup.yml` flow locally.

```
usage: gh tt deliver
```

`deliver` squeezes all the commits on the issue branch into one commit (using `git commit-tree HEAD^{tree}` since `main`) and pushes it to the remote on a new `ready/<ISSUE_BRANCH>` branch. A seperate workflow `.github/workflows/ready.yml` is defined to pick this up, run additional tests and fast-forward onto `main`

When an issue branch is `delivered` the issue is automatically closed. there is a git alias defined `git sweep` which will prune and delete all local branches that are deliverd and reset to `main`.


## Annotate summaries to issues

When annotating summaries using to issues using github flavoured MarkDown (`gh issue comment`), please consider the following:

Unescaped backticks meant to mark code blocks and inline code, are likely to be mistaken as command substitutions. So for that reason don't use `--body` flag to commands like `gh issue create` and  `gh issue comment`. Instead generate the markdown in intermediate `*.md` files in the `./temp` folder and use the `--body-file` flag instead. 

Name the file the same as the branch we're working on, with a `.md` extension, and store it in the `./temp` folder. Open it in the editor for my review and annotations before posting it to the issue.


When in @github agent mode and I ask to _annotate a comment on the current changeset to the issue_ you can always read the implied issue number from the current git branch - development branches are prefixed with an integer, and that is a reference to the issue being worked on. The branch name is part of the zsh prompt in the @terminal, and can be directly accessed. 

Do not summarize based on our conversation or individual commits on the issue branch. Instead summarise on the accumulated changes - the actual changeset - since we left `main` (equivalent to `git diff main...HEAD`).

Make it a high-level overview of what was done (describe the changes), why it was done (the rationale behind our decisions), and any relevant context (maybe external links of general architectural or design decisions). The summary should have the header `##Change log summary` and even if I asked you to create such a summary earlier on this branch, you should still create the full summary again (don't just summarize the increment since last).

The purpose of the summary is to help my future self and current team mates to recall and understand the purpose of - and rationale behind - the changes without needing to read through all the code or commit messages.

# Code style and design principles

## CLI output and print statements
In general avoid adding print statements. We're developing a CLI for developers and we usually do not like verbose informative statements. If nothing happened, then nothing should be printed. I'll let you know explicitly when print statements are needed.

## DRY - Don't Repeat Yourself
Avoid code duplication. If you find yourself copy-pasting code, then it's a sign that you should refactor the code into a function or class that can be reused.

## Keep changesets small and focused
When working on an issue,  keep the changeset small and focused on the issue at hand. Do not add unrelated changes or refactorings. 

## Suggest new issues
Feel free to point out code smells and suggest improvements, but do not implement them unless they are directly related to the issue. If they are severe and important enough, then offer to create a new issue for them. Follow the same approas as when you annotate summaries to issues comments (create a `*.md` file in the `temp` folder. create the issue using the `--body-file` flag).

## Favor testable code
When writing code, favor testable code. This means that you should write code that can be easily tested with unit tests. Avoid writing code that is tightly coupled or has side effects that are hard to mock or stub.

## Offer to write tests
If you find that the code you're working on is not well tested, then offer to write tests for it. But to not write the tests unless I explicitly ask you to do so.


