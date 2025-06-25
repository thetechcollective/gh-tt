import os
import sys
import re
import json
import asyncio


from gitter import Gitter
from lazyload import Lazyload



def deep_update(dict1, dict2):
    """Recursively update dict1 with dict2 without deleting keys."""
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
            deep_update(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def add_config(config_file: str, config_dict: dict):

    """Helper function to update the configuration dictionary and add it to the input parameter
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

def load_default_configuration(config_file_name: str, config_dict: dict, config_files: list):
    # Default configuration file MUST exist
    default_config_path = os.path.dirname(os.path.abspath(__file__)) + f"/{config_file_name}"
    assert os.path.exists(default_config_path), f"Default config file '{default_config_path}' not found."

    # Initialize with defaults
    config_dict = add_config(default_config_path, config_dict)
    config_files.append(default_config_path)

    return config_dict, config_files


class Config(Lazyload):
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

    _config_dict, _config_files = load_default_configuration(
        config_file_name=_config_file_name,
        config_dict=_config_dict,
        config_files=_config_files
    )

    @classmethod
    def config_files(cls):
        """Reveals the configuration files used by the class.
        Returns:
            list: List of configuration files in the order they are loaded
        """
        return cls._config_files

    @classmethod
    def config(cls, load_only_default: bool = False) -> dict:
        """Public class property to get the config dict"""

        if load_only_default:
            return cls._config_dict
        
        _project_config_file = f"{Gitter.git_root}/{cls._config_file_name}"

        if os.path.exists(_project_config_file):
            cls._config_dict = add_config(_project_config_file, cls._config_dict)
            cls._config_files.append(_project_config_file)

        cls.__assert_required(_project_config_file)

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
    
    @classmethod
    def clear_config(cls):
        """Assigns empty values to class properties"""

        cls._config_dict = {}
        cls._config_files = []

        # Reload the default configuration
        cls._config_dict, cls._config_files = load_default_configuration(
            config_file_name=cls._config_file_name,
            config_dict=cls._config_dict,
            config_files=cls._config_files
        )

    @classmethod
    def __assert_required(cls, config_path: str):
        props_set_from_gitconfig = []
        gitconfig_file = f"{Gitter.git_root}/.gitconfig"

        project_owner = None
        project_number = None

        if not cls._config_dict.get('project', {}).get('owner'):
            project_owner = asyncio.run(cls()._run('project_owner', args={'gitconfig_file': gitconfig_file}))
            if project_owner:
                props_set_from_gitconfig.append('project_owner')

        if not cls._config_dict.get('project', {}).get('number'):
            project_number = asyncio.run(cls()._run('project_number', args={'gitconfig_file': gitconfig_file}))
            if project_number:
                props_set_from_gitconfig.append('project_number')
        
        if props_set_from_gitconfig:
            print(f"⚠️  DEPRECATED: .gitconfig based configuration is deprecated.")
            print(f"🔨  Your {config_path} file will be updated with values found in .gitconfig.")
            print(f"⚠️  Review the updated {config_path} and consider checking it in.")

            data = {}
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        print(f"🛑 ERROR: Could not parse existing config file.", file=sys.stderr)
                        sys.exit(1)

            data["project"] = data.get("project", {})

            if project_owner is not None:
                data["project"]["owner"] = data["project"].get("owner", project_owner)

            if project_number is not None:
                data["project"]["number"] = data["project"].get("number", int(project_number))

            with open(config_path, "w") as file:
                json.dump(data, file, indent=4)

            add_config(config_path, cls._config_dict)

        if not all([cls._config_dict['project']['owner'], cls._config_dict['project']['number']]):
            print(f"🛑 ERROR: Could not load information about project owner or project number from configuration. Missing values are not currently supported. Please specify a 'project' key with 'owner' and 'number' key-value pairs in .tt-config.json.")
            sys.exit(1)