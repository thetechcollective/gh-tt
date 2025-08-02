---
applyTo: '**'
---
When in agent mode, creating intermediate or temporary test files, always create them in the ./temp folder which is ignored by git

In general avoid being too generous when suggesting print statements. We're developing a CLI for developers and we usually do not like verbose informative statements. If nothing happened, then nothing should be printed. I'll let you know explicitly when print statements are needed.

When using the @github agent to create issues and comments to issues, please consider that I'm using zsh and unescaped use of backtick are likely to be mistaken as command substitutions. So for that reason prefer to generate the markdown in intermediate `*.md` files in the `./temp` folder and restrain from using the `--body` flag to `gh issue create` and  `gh issue comment` when you markdow contains backticks. But favor the `--body-file` flag instead.

When in @github agent mode and I ask to _annotate a comment on the curret changeset to the issue_ you can always read the implied issue number from the current git branch - development branches are prefixed with an integer, and that is a reference to the issue being worked on.