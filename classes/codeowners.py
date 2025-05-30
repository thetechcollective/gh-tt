from gitter import Gitter
import os
import sys
import re
import json
import asyncio


# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

# Module level helper functions


def codeowners_file_to_dict(codeowner_file: str) -> dict:
    """Helper function to read the CODEOWNERS file, load it into a dict and in the process convert the glob patterrns to RegExp patterns
    Args:
        file (str): The path to the CODEONERS file to parse
    """

    # Each line is expected to be in the format:
    # <file-glob> <owner1> [<owner2> ... <ownerN>]
    # for each file glob, convert it to a regular expression and add it to the dictionary
    # Undet that key add a list of owners
    codeowners_dict = {}
    with open(codeowner_file, 'r') as f:
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
        codeowners_dict[file_glob] = owners
    return codeowners_dict


# READ ALL ABOUT IT:
# https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
class Codeowners():
    """Class used to represent the CODEOWNERS file and offers features to match files against ownership.
    """

    # Class-level configuration dictionary
    _codeowners_dict = {}
    _codeowners_files = []  # List to hold the configuration files in the order they are read
    _codeowners_file_name = 'CODEOWNERS'

    _repo_root = Gitter.git_root

    # Scan through the three locations for the CODEOWNERS file
    _valid_locations = [
        f"{_repo_root}/.github/{_codeowners_file_name}",
        f"{_repo_root}/{_codeowners_file_name}",
        f"{_repo_root}/docs/{_codeowners_file_name}"
    ]

    for _location in _valid_locations:
        if os.path.exists(_location):
            _codeowners_files.append(_location)

    if len(_codeowners_files) > 0:
        if len(_codeowners_files) > 1:
            print(
                f"""⚠️ Multiple CODEOWNERS files found. Using the first one found: '{_codeowners_files[0]}'.\n💡 Valid locations listed in search order:\n- {'\n- '.join(_valid_locations)}""", file=sys.stderr)

        _codeowners_dict = codeowners_file_to_dict(_codeowners_files[0])

    @classmethod
    def file_location(cls, all=False):
        """Reveals the configuration files used.
        Returns:
            list: List of configuration files in the order they are loaded
        """
        if all:
            return cls._codeowners_files

        return cls._codeowners_files[0]

    @classmethod
    def search_order(cls):
        """Reveals the searchorder of the valid locations of the CODEOWNERS file
        """
        return cls._valid_locations

    @classmethod
    def codeowner_json(cls) -> dict:
        """The CODEOWNERS converted to a JSON dictionary. and globs are converted to regular expressions."""
        return cls._codeowners_dict

    @classmethod
    def codeowner_parse(cls, changeset: list[str], exclude: list[str] = None) -> list[str]:
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
            for pattern, pattern_owners in reversed(list(cls._codeowners_dict.items())):
                if re.match(pattern, file_path):
                    # Exclude owners in the exclude list
                    filtered_owners = [
                        o for o in pattern_owners if o not in exclude]
                    if filtered_owners:
                        result.append(f"{file_path} ({','.join(filtered_owners)})")
                    break 
        return result

    @classmethod
    def codeowner_parse_string(cls, changeset: str) -> str:
        """Parse a string of file changes and return a string of owners for each file.

        Args:
            changeset (str): String of file paths to check ownership for, separated by newlines.

        Returns:
            str: String of files that have owners, with owners listed in paranthesis.
            If no owners are found, the file is not included in the list.
        """
        changeset = changeset.strip().split('\n')
        return '\n'.join(cls.codeowner_parse(changeset))
