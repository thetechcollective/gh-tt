---
applyTo: '**'
---
When using the @github agent to create issues and comments to issues, please consider that I'm using zsh and unescaped use of backtick are likely to be mistaken as command substitutions. So for that reason prefer to generate the markdown in intermediate `*.md` files in the `./temp` folder and restrain from using the `--body` flag to `gh issue create` and  `gh issue comment` when you markdown contains backticks. But favor the `--body-file` flag instead. Name the file the same as the branch we're working on, with a `.md` extension, and store it in the `./temp` folder. Open it in the editor for my review and annotations.

When in @github agent mode and I ask to _annotate a comment on the current changeset to the issue_ you can always read the implied issue number from the current git branch - development branches are prefixed with an integer, and that is a reference to the issue being worked on. The branch name is part of the zsh prompt in the @terminal, and can be directly accessed; The `$PS1` is set up to show the branch name too (e.g. `vscode ➜ /workspaces/gh-tt (321-Update_summary_instructions) $` equals issue 321). Let summary serve as a work log note to future self and current colleagues. It should summarize the changes made in the branch we're working on (including any dirty files) since we left `main` (equivalent to `git diff main...HEAD`).

Only summarize on the accumulated change set in the branch. Do not dive into - or reference - the individual commits on the branch. The branch will be squashed into one commit before it hits main so not BOM (Bill of Material) is need - just a summary in prose. Make it a high-level overview of what was done (describe the changes), why it was done (the rationale behind our decisions), and any relevant context (maybe external links of general architectural or design decisions). The summary should have the header `##Change log summary` and even if I did ask you to create such a summary earlier on this branch, you should create the full summary again (don't just summarize the increment since last).

The purpose of the summary is to help my future self and current team mates to recall and understand the purpose of - and rationale behind - the changes without needing to read through all the code or commit messages.

Workflow for efficient summary creation and posting:
1. Extract issue number directly from branch name with a single command (no need for multiple tool calls)
2. Create the summary file directly without asking for confirmation or explaining each step
3. Post the comment using the `--body-file` flag without excessive explanation
4. Confirm success with just the URL of the posted comment

This streamlined process should minimize back-and-forth exchanges and unnecessary explanation of each step.

