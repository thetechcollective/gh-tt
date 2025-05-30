# `CODEOWNERS`

GitHub implements support for  a file `CODEOWNERS` the purpose is then, for a repository to add a policy to the Pull Requests that files _owned_ by someone should be reviewed by the owners.

The idea is good, but the implemntation in GitHub is troublesome.

1. GitHub only supports the `CODEOWNERS` file in Pull Requests
2. If ownership is given to a group, or more than one handle, this is interpreted that _everyone_ in then group or list must approve.
3. The documentation says that the `CODEOWNERS` file uses globs that [_follws most of the same rules used in `.gitignore` files_](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners#codeowners-syntax). But how it differs from globs used in `.gitignore` is not clear. It's documented by an example only.

## Our own parser to the rescue

We need the following features

1. Our regime is not one that uses _peer reviews_ as quality gates. On the contrary we adhere to XP like values, based on paired – or even mob – programing and we would like to enage the _code owners_ already during development, when someone changes files, that has ownership, the owners should join or mentor the development of that particular branch. _During_ as aoopsed to _after_. We need to support and parse the `CODEOWNERS` file, when commits are don to development branches.
2. We interpret multiple owership or ownership to teams in a more trusting manner. If a developer is a member of a team of _owners_, then an additional approval, from another mebers should not be required.
3. We interpret the `CODEOWNERS` file with support of only two patterns from the [`.gitignore` pattern format documentation](https://git-scm.com/docs/gitignore#_pattern_format);  `*` and `**` (described in some detail later). 

## `codepwners.py``

A purely static class, all methods are class methods.
It reads the `CODEOWNER` files from the supported locations: the search order is:

### Locations    
1. `<repo-root>/.github/`
2. `<repo-root>`
3. `<repo-root>/docs/`
    
The search stops when a file named `CODEOWNERS` is found in any of the locations.

### Parsing
Each line in the `CODOWNERS` file is then read, - to the end - and during parsing it is read from bottom up. 

In other words; if more patterns would defines ownership to the same file, it's the latest one, that is used to determine the ownership of a file.

### Format

`CODEOWNERS` file can contain:

  - _comments;_ defined as lines with `#` the first non white-space character.
  - _in-line commentes;_ Anything following `#` is stripped.
  - _empty lines;_ Lines that contains noting or only whitespaces

Each line has the following format:

```
<file-pattern> <owner1> [<owner2> ... <ownerN>]`
```

Where:
  - `<file-pattern>` is a glob pattern that matches files in the repository
  - `<owner1>, <owner2>, ..., <ownerN>` are GitHub usernames, team names or emails 

user names and team names must be prefixed with `@` and team names must be fully qualified with `@<org>/<team-name>`.

Glob patterns:

The glob patterns are used to match files in the repository. is consistent with how git handles glob patterns in 
the `.gitignore` file. Globbing is simple (at first) only two globs are supported:

  - '*'  matches zero or more characters, but not across directory boundaries.
  - '**' matches zero or more directories.

The simplifed (but complete)  break down of the glob patterns is as follows:

'*' is requvivlanetn to the RegExp [^/]*. With offset i the `<repo-root> it will match files and directories in the same directory but it won't descend into subdirectories.

'**' is equivalent to the RegExp .*\/. It will match files and directories in the same directory as the .gitignore file, as well as any files and directories in subdirectories, and so on recursively.
    
    
Example:
```
    project/
    ├── .gitignore
    ├── file1.txt
    ├── dir1/
    │   ├── file2.txt
    │   └── dir2/
    │       └── file3.txt
    └── file4.txt
```

Globs:
```
    *.txt
    dir1/*
````

Parser:
```
    - file1.txt and file4.txt will be ignored because of *.txt.
    - file2.txt will be ignored because of dir1/*.
    - dir2/file3.txt will not be ignored because * does not cross directory boundaries.
````

to match any *.txt file - across directory boundaries (which may have been the semantical intent by the first glob) 
you would use the glob:

```    
    **/*.txt
```    
This will match any .txt file in the repository, regardless of its location.
