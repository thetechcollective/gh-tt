import asyncio
import json
import os
import re
import subprocess
import sys

from gh_tt.classes.gitter import Gitter
from gh_tt.classes.lazyload import Lazyload

# Module level helper functions


def responsibles_file_to_dict(responsibles_file: str) -> dict:
    """Helper function to read the RESPONSIBLES file, load it into a dict and in the process convert the glob patterrns to RegExp patterns
    Args:
        file (str): The path to the RESPONSIBLES file to parse
    """

    # Each line is expected to be in the format:
    # <file-glob> <owner1> [<owner2> ... <ownerN>]
    # for each file glob, convert it to a regular expression and add it to the dictionary
    # Undet that key add a list of owners
    responsibles_dict = {}
    with open(responsibles_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        if re.match(r'^\s*#', line):
            continue  # Skip comment lines
        # Strip inline comments
        line = re.sub(r'\s*#.*$', '', line).strip()  # Remove inline comments
        parts = line.split()
        file_glob = parts[0]
        owners = parts[1:]

       #TODO
        #Literal .
        #Literal /

        # Remove any leading or trailing whitespace from owner names
        owners = [o.strip() for o in owners]

        # Convert the glob pattern to a regular expression
        # replace '/' with '|' to process later 
        file_glob = re.sub(r'\/', r'|', file_glob)

        # use negeative and positive lookbehind and lookahead to make replace solitoire '* with @ ...for later processing 
        file_glob = re.sub(r'(?<!\*)\*(?!\*)', '@', file_glob)

        # Repplace '.' with '\.' (to match a literal dot)
        file_glob = re.sub(r'\.', r'[.]', file_glob) 

        # Replace '**' with '.*' (to match any string)
        file_glob = re.sub(r'(?<!\*)\*\*(?!\*)', '.*', file_glob)

        # Replace '@' - originally '*' with '[^/]*' (to match any string that does not contain a slash)
        file_glob = re.sub(r'@', '[^/]*', file_glob)

        # Repalce '@' with '.*\/' (to match any string the ends with a slash)
        file_glob = re.sub(r'\|', '[\\/]?', file_glob)
        
        # Add to the dictionary
        responsibles_dict[file_glob] = owners
    return responsibles_dict


# READ ALL ABOUT IT:
# https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
class Responsibles():
    """Class used to represent the RESPONSIBLES file and offers features to match files against ownership.
    """

    # Class-level configuration dictionary
    _responsibles_dict = {}
    _responsibles_files = []  # List to hold the configuration files in the order they are read
    _responsibles_file_name = 'RESPONSIBLES'

    _repo_root = Gitter.git_root

    # Scan through the three locations for the RESPONSIBLES file
    _valid_locations = [
        f"{_repo_root}/.github/{_responsibles_file_name}",
        f"{_repo_root}/{_responsibles_file_name}",
        f"{_repo_root}/docs/{_responsibles_file_name}"
    ]

    for _location in _valid_locations:
        if os.path.exists(_location):
            _responsibles_files.append(_location)

    if len(_responsibles_files) > 0:
        if len(_responsibles_files) > 1:
            new_line = '\n'
            print(
                f"""⚠️ Multiple RESPONSIBLES files found. Using the first one found: '{_responsibles_files[0]}'.\n💡 Valid locations listed in search order:\n{new_line.join(_valid_locations)}""", file=sys.stderr)

        _responsibles_dict = responsibles_file_to_dict(_responsibles_files[0])

    @classmethod
    def file_location(cls, all=False):
        """Reveals the configuration files used.
        Returns:
            list: List of configuration files in the order they are loaded
        """
        if all:
            return cls._responsibles_files

        return cls._responsibles_files[0]

    @classmethod
    def search_order(cls):
        """Reveals the searchorder of the valid locations of the RESPONSIBLES file
        """
        return cls._valid_locations

    @classmethod
    def responsibles_json(cls) -> dict:
        """The RESPONSIBLES converted to a JSON dictionary. and globs are converted to regular expressions."""
        return cls._responsibles_dict

    @classmethod
    def codeowners_parse(cls, changeset: list[str], exclude: list[str] = None) -> list[str]:
        """Parse a list of file changes and return a list of owners for each file.

        Args:
            changeset (list[str]): List of file paths to check ownership for.

        Returns:
            list: List of files that have owners, with owners listed in paranthesis.
            If no owners are found, the file is not included in the list.
        """
        result = []

        if exclude is None:
            exclude = []

        # Iterate over each file in the changeset
        for file_path in changeset:
            filtered_owners = []
            # Go through the regex patterns in reverse order (bottom up)
            for pattern, pattern_owners in reversed(list(cls._responsibles_dict.items())):
                if re.match(pattern, file_path):
                    # Exclude owners in the exclude list
                    filtered_owners = [
                        o for o in pattern_owners if o not in exclude]
                    if filtered_owners:
                        result.append(f"{file_path} ({','.join(filtered_owners)})")
                    break 
        return result


    @classmethod
    def responsibles_parse(cls, changeset: list[str], exclude: list[str] = None) -> list[str]:
        """Parse a list of file changes and return a list of responsibles for each file.

        Args:
            changeset (list[str]): List of file paths to check responsibility for.

        Returns:
            list: List of files that have responsibles - after the exclusion.
        """
        result = []
        if exclude is None:
            exclude = []

        # Iterate over each file in the changeset
        for file_path in changeset:
            # Go through the regex patterns in reverse order (bottom up)
            for pattern, responsibles in reversed(list(cls._responsibles_dict.items())):
                if re.match(pattern, file_path):
                    # This files has responsibles.
                    excluded = False
                    # for each item in exclude, check if the item is in the responsibles
                    # If it is, set excluded to True
                    for e in exclude:
                        if e in responsibles:
                            excluded = True
                            break

                    if not excluded:
                        result.append(f"{file_path} ({','.join(responsibles)})")

                    break 
        return result
    
    @classmethod
    def responsibles_as_markdown(cls, changeset: list[str], exclude: list[str] = None) -> str:
        """Parse a list of file changes and return a markdown formatted list of responsibles for each file.

        Args:
            changeset (list[str]): List of file paths to check responsibility for.

        Returns:
            str: Markdown formatted list of files that have responsibles.
            If no owners are found, the file is not included in the list.
        """
        filelist = cls.responsibles_parse(changeset, exclude)

        # Return a bulleted list with each item in file list. wrap the first item in backticks
        if not filelist:
            return None
        markdown_list = []  
        for item in filelist:
            # Split the item into file path and responsibles
            file_path, responsibles = item.split(' (', 1)
            responsibles = responsibles.rstrip(')')
            # Format the item as a markdown list item
            markdown_list.append(f"- `{file_path}` ({responsibles})")
        # Join the list items with newlines
#        return "\n".join(markdown_list)

        new_line = '\n'
    
        return f"{cls.responsibles_markdown_prefix()}\n\n{new_line.join(markdown_list)}\n\n" 

    @classmethod
    def responsibles_markdown_prefix(cls):
        return "**Responsibles for the changeset:**"
