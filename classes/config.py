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

def deep_update(dict1, dict2):
    """Recursively update dict1 with dict2 without deleting keys."""
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
            deep_update(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def add_config(config_file: str, config_dict: dict):

    """Helper function to update the configuration dictionary and add it to the input paramaeter
    Args:
        file (str): The path to the config file to add
    Raises:
        FileNotFoundError: If the file does not exist
        JSONDecodeError: If the file is not a valid JSON file
    """
    with open(config_file, 'r') as f:
        try:
            lines = f.readlines()
            lines = [line for line in lines if not re.match(r'^\s*//', line)]
            config_data = ''.join(lines)
            json_data = json.loads(config_data)
            deep_update(config_dict, json_data)
        except json.JSONDecodeError as e:
            print(f"Could not parse JSON from {config_file}: {e}", file=sys.stderr)
            sys.exit(1)              
    return config_dict

class Config():
    """Class used to represent the project configuration and policies for the subcommands.
    
    Purely static class, all methods are class methods.
    It reads the configuration from a JSON file, which may contain comments.
    The configuration file is expected to be in the root directory of the git repository.
    The configuration file is expected to be a JSON file with comments (lines beginning with '//').
    """

    # Class-level configuration dictionary
    _config_dict = {}
    _config_files = []  # List to hold the configuration files in the order they are read
    _config_file_name = '.tt-config.json'

    # Default configuration file name MUST exist in the source code root directory (one level up from this file)
    _app_config_file = os.path.dirname(os.path.abspath(__file__)) + f"/../{_config_file_name}"
    assert os.path.exists(_app_config_file), f"Application config file '{_app_config_file}' not found."

    _config_dict = add_config(_app_config_file, _config_dict)
    _config_files.append(_app_config_file)  

    # Add the project default config file if it exists
    _project_config_file = f"{Gitter.git_root}/{_config_file_name}"
    if os.path.exists(_project_config_file):
        _config_dict = add_config(_project_config_file, _config_dict)
        _config_files.append(_project_config_file)  

    @classmethod
    def config_files(cls):
        """Reveals the configuration files used by the class.
        Returns:
            list: List of configuration files in the order they are loaded
        """
        return cls._config_files

    @classmethod
    def config(cls) -> dict:
        """Public class property to get the config dict"""
        return cls._config_dict
    
    @classmethod
    def add_config(cls, config_file: str):
        """Public classmethod to update the configuration dictionary and add a config file to the list of config files
        Args:
            file (str): The path to the config file to add
        Raises:
            FileNotFoundError: If the file does not exist
            JSONDecodeError: If the file is not a valid JSON file
        """

        add_config(config_file, cls._config_dict)
        cls._config_files.append(config_file)
        return cls._config_dict