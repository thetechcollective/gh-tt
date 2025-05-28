# `codewners.py`


Purely static class, all methods are class methods.
It reads the CODEOWNER files from the supported locations: the search order is:
    
1. `<repo-root>/.github/`
2. `<repo-root>`
3. `<repo-root>/docs/`
    
The search stops when a file named `CODEOWNERS` is found in any of the locations

Each line in the `CODOWNERS` file is then read, - to the end - and during parsing it is read from bottom up. 
In other words, the last matching line is the one that is used to determine the ownership of a file.

`CODEOWNERS` file can contain 
  - _comments;_ defined as lines with `#` the first non white-space character.
  - _in-line commentes;_ Anything following `#` is stripped.
  - _empty lines;_ Lines that contains noting or only whitespaces

Each line has the following format:
`<file-pattern> <owner1> [<owner2> ... <ownerN>]`

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
