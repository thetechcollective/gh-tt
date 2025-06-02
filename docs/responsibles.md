# `RESPONSIBLES`

## GitHub `CODEOWNERS` as inspiration

GitHub supports a file called `CODEOWNERS`. When defined, a repository can add a policy to Pull Requests that parses the `CODEOWNERS` file against the actual files changed in the commit. If any files are _owned_ by someone, GitHub enforces a review and awaits approval.

The idea is good, but the implementation in GitHub is troublesome:

1. GitHub only supports parsing the `CODEOWNERS` file in Pull Requests.
2. If ownership is given to a group or more than one handle, this is interpreted as _everyone_ in the group or list must approve.
3. The documentation says that the `CODEOWNERS` file uses globs that [_follow most of the same rules used in `.gitignore` files_](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners#codeowners-syntax). However, how it differs from globs used in `.gitignore` is not clear. It's documented by example only.

## Our own alternative `RESPONSIBLES` parser

We need the following features:

1. Our process does not use _peer reviews_ as quality gates. On the contrary, we believe that enforcing _hand-overs_ in a process leads to waste in terms of _unevenness_, _overburden_, and ultimately _poor quality_. In our team, we adhere to XP-like values, based on paired – or even mob – programming, and we work with a concept we call _Module Key Responsible (MKR)_. Each repo has exactly _one_ MKR, who have the oppotunity to delegate some responsibility to others. Inspired by the _Benevolent Dictator Governance_ model well-known from many Open Source communities, we aim to engage _responsibles_ already during development. We need the feature that when someone changes files with appointed responsibility, (one of) the responsibles should join or mentor the development of that branch. We want this to happen _during_ development, not _after_. This should happen when commits are made to development branches.
2. We interpret multiple responsibles in a more trusting manner. Contrary to GitHub's `CODEOWNERS`, which requires approval from _all_ code owners, we call for _eyes-on-code_ and _mentorship_ from _one of_ the responsibles. We do not enforce arbitrary wait-states. A review is not a quality gate; it's a collaboration tool.
3. Due to the somewhat undocumented semantics of GitHub's `CODEOWNERS` file, we have introduced our own format: `RESPONSIBLES`. We believe we can achieve what we seek with only two simple glob patterns from the [`.gitignore` pattern format documentation](https://git-scm.com/docs/gitignore#_pattern_format): `*` and `**` (described in detail later).

## The `RESPONSIBLES` file

The `RESPONSIBLES` file can be stored in different supportedf locations — using the same search order as GitHub uses for the `CODEOWNERS` file:

1. `<repo-root>/.github/`
2. `<repo-root>`
3. `<repo-root>/docs/`

The search stops on the first match of a file named `RESPONSIBLES` in any of the locations.

### Parsing

During parsing, the `RESPONSIBLES` file is read from bottom up.

In other words, if multiple patterns define responsibles for the same file, the latest one is used to determine the responsible(s) for a file.

### Format

A `RESPONSIBLES` file can contain:

- _Comments:_ Lines where `#` is the first non-whitespace character.
- _Inline comments:_ Anything following `#` is stripped.
- _Empty lines:_ Lines that contain nothing or only whitespace.

Each line has the following format:

```
<file-pattern> <owner1> [<owner2> ... <ownerN>]
```

Where:

- `<file-pattern>` is a glob pattern that matches files in the repository.
- `<owner1> <owner2> ... <ownerN>` are GitHub usernames, separated by whitespace (not commas!).

Usernames must be prefixed with `@` (e.g., `@lakruzz`).

Contrary to GitHub's `CODEOWNERS`, we do not support teams or emails. This is by deliberate choice: Teams can be secret or private, and it's not always possible for everyone to look up who's a member of a given team. Also, it defies our philosophy that a _team_ can be responsible. It's _one_ MKR that's responsible, and the MKR may have delegated some responsibility to others, but these are also named individuals.

### Glob patterns

The glob patterns are used to match files in the repository. They are consistent with how git handles glob patterns in the `.gitignore` file, but only a small subset of the features is implemented.

Globbing is simple: only two globs are supported:

- `*` matches zero or more characters, but not across directory boundaries.
- `**` matches zero or more directories.

The simplified (but complete) breakdown of the glob patterns is as follows:

- `*` is equivalent to the RegExp `[^/\\]*` (matches any character except slash or backslash). With offset in the `<repo-root>`, it will match _files_ but not _directories_.
- `**` is equivalent to the RegExp `.*`. It will match _any or no character_, including slashes, so contrary to `*`, the `**` glob will match _directories_ and _files_ alike.
- `/` is translated to RegExp `[/\\]?`, matching _zero or one_ of either a slash or a backslash.
- Anything else is considered a literal and needs an exact match to define responsibility.

Example file tree:

```
project/
├── RESPONSIBLES
├── file1.txt
├── dir1/
│   ├── file2.txt
│   └── dir2/
│       └── file3.txt
└── file4.txt
```

RESPONSIBLES:

```
*.txt @lakruzz
dir1/* @albertbanke @lakruzz
```

Parser:

- `file1.txt` and `file4.txt` have `@lakruzz` as responsible.
- `file2.txt` has `@albertbanke @lakruzz` as joint responsibles.
- `dir2/file3.txt` is not under any explicit responsibility.

Since `*` doesn't descend into directories, `*.txt` only matches files in the repo root.

To match any `.txt` file across directory boundaries (which may have been the intended semantics of the first glob), you would use the glob:

```
**/*.txt
```

This will match any `.txt` file in the repository, regardless of its location.

### Semantics

The committer has already approved: If `@lakruzz` changes `file.txt`, it will _not_ trigger an involvement, simply because we imply involvement from the committer.

## One or more responsibles

If an ownership lists more than one responsible, then _all_ responsibles will be invited to the issue, but if the committer is _any_ of the responsibles, then _none_ will be invited. This follows the same logic that implies involvement from the committer.

From the example above:

`dir1/* @albertbanke @lakruzz`

If either `@lakruzz` or `@albertbanke` is the committer of `file2.txt`, then no trigger is fired. But if `@ravvnen` is the committer, then both `@lakruzz` and `@albertbanke` will receive a mention on the issue `@ravvnen` is working on.

## What if approval from _both_ is required?

That is currently not supported – and probably never will be, since that would imply a review/approval paradigm. This is known to cause inefficient wait states in the process.
