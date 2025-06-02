# `RESPONSIBLES`


## GitHub `CODEOWNERS`as inspiration
GitHub implements support for  a file `CODEOWNERS`. When defined, a repository can add a policy to the Pull Requests that will parse the `CODEOWNERS` file agains actual files changed in the commit. And if any files are _owned_ by someone enforce a review and await approval.

The idea is good, but the implemntation in GitHub is troublesome.

1. GitHub only supports parsing the `CODEOWNERS` file in Pull Requests
2. If ownership is given to a group, or more than one handle, this is interpreted that _everyone_ in then group or list must approve.
3. The documentation says that the `CODEOWNERS` file uses globs that [_follws most of the same rules used in `.gitignore` files_](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners#codeowners-syntax). But how it differs from globs used in `.gitignore` is not clear. It's documented by an example only.

## Our own alternative `RESPONSIBLES` parser to the rescue

We need the following features:

1. Our regime is not one that uses _peer reviews_ as quality gates. On the contrary we belive that enforcing _hand-overs_ in a process leads to waste in the process in terms of _unevenness_, _overburdenness_ and in the end poor quality. In our team we adhere to XP like values, based on paired – or even mob – programing and we work with a concept we call _Module Key responsible (MKR)_. Each repo has exactly _one_ and MKRs can delegate some of this responsibilty to others. Inspired by the _Benevolent Dictator Goververnance_ well-known from plenty of Open Source communitites. We aim to engange _responsibles_ already during development. We need the feature that when someone changes files, that has appointed responsibility, (one of) the responsibles should join or mentor the development of that particular development branch. We want this to happen _during_ as aoopsed to _after_. We need this to hammen when commits are done to development branches.
2. We interpret multiple responsibles in a more trusting manner. Contrary to GitHub's `CODEOWNERS` who needs an approval from _all_ code owners, we require _eyes-on-code_ and _mentorship_ from _one of_ the responsibles. We are not enforcing arbitrary wait-states. A review is not a quality gate, it's a collaboration tool.
3. Due to the somewhat undocumented semantics of GitHub's `CODEOWNERS` file we have introduced our own format `RESPONSIBLES`.  We belive we can achieve what we seek with only two simple glob pattersns from the [`.gitignore` pattern format documentation](https://git-scm.com/docs/gitignore#_pattern_format);  `*` and `**` (described in some detail later). 

## `responsibles.py`

A purely static class, all methods are class methods.
It reads the `RESPONSIBLES` files from the supported locations: the search order is teh same as GitHub uses for the `CODEOWNERS` file:

### Locations    
1. `<repo-root>/.github/`
2. `<repo-root>`
3. `<repo-root>/docs/`
    
The search stops when a file named `RESPONSIBLES` is found in any of the locations.

### Parsing
During parsing the `RESPONSIBLES` file is read from bottom up. 

In other words; if more patterns would define responsibles to the same file, it's the latest one, that is used to determine the the responsible of a file.

### Format

`RESPONSIBLES` file can contain:

  - _comments;_ defined as lines with `#` the first non white-space character.
  - _in-line commentes;_ Anything following `#` is stripped.
  - _empty lines;_ Lines that contains noting or only whitespaces

Each line has the following format:

```
<file-pattern> <owner1> [<owner2> ... <ownerN>]`
```

Where:
  - `<file-pattern>` is a glob pattern that matches files in the repository
  - `<owner1> <owner2> ... <ownerN>` are GitHub user names. Seperated by white-spaces (not commas!) 

User names must be prefixed with `@` (e.g `@lakruzz`).

Contrary to GitHub's `CODEOWNERS` we do not support teams or emails. This is by deliberate choice: Teams can be secret or private and it's not always possible for everyone to look-up who's a member of a given team. Also it's defies our filosofy, that a _team_ can be responsible. It's _one_ MKR that's responsible and the MKR may have delegated – some – responsibility to others. But these are also named individuals.

### Glob patterns:

The glob patterns are used to match files in the repository. It is consistent with how git handles glob patterns in the `.gitignore` file – but it only implements a very small subset of the feature.

Globbing is simple (at first) only two globs are supported:

  - '*'  matches zero or more characters, but not across directory boundaries.
  - '**' matches zero or more directories.

The simplifed (but complete) break down of the glob patterns is as follows:

`*` is equvivalent to the RegExp `[^/^\]*`(matches any char - except slash or backslashes). With offset in the `<repo-root> it will match _files_ but consequently not _directories_.

`**` is equivalent to the RegExp `.*` It will match _any or non character_ including slashes, so contrary to `*` the `**` glob will match _directories_ and _files_ alike.

`/` is translateed to RegExp `[/\]?` matchin _zero or none_ of either a slash or a backslash.

Enything else is considered literals. and needs an exact match to define responsiblity. 

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
```
    - `file1.txt` and `file4.txt` have `@lakruzz` as responsible
    - `file2.txt` have ` @albertbanke @lakruzz` as joint responsibles
    - `dir2/file3.txt` are not under any explicit responsiblity
```

Since `*` doesn't descned into directories, `*.txt` only matches files in the repo-root. 

To match any `.txt` file - across directory boundaries (which may have been the semantical intent by the first glob) you would use the glob:

```    
    **/*.txt
```    
This will match any `.txt` file in the repository, regardless of its location.

### Semantics

The comitter has already aproved: If `@lakruzz` changes `file.txt` it will _not_ trigger an envolvement, simply because we imply envolvelment from the committer.

## Ono or more responsibles

If an ownership lists more than one responsible, then _all_ responsibles will be inviteed to the issue, but if the committer ins _any_  of the responsibles, then _none_ will be invited. Following the same logic that imply envolvelment from the committer.

From the example above:

`dir1/* @albertbanke @lakruzz`


If either `@lakruzz` or `@albertbanke` is the comitter of `file1.txt` then no trigger is fired. But if `@ravvnen` is the committer, then both `@lakruzz` and `@albertbanke` will recieve a mention on the issue `@ravvnen` is working on.

## What if approval from _both_ is required

That is currently not supported – and probably never will be. Since that would imply a review/approval paradigm. This is know to cause inefficient wait states ine the process. 