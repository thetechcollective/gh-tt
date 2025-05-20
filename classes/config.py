from lazyload import Lazyload
from gitter import Gitter
import os
import sys
import re
import json

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Config(Lazyload):
    """Class used to represent the project configuration and policies for the subcommands."""

    # Instance methods

    def __init__(self, file=None):
        super().__init__()


        self.set('default_configfile', '.tt-config.json' )
        self.set('workdir', os.getcwd())
        self.set('config_files', [])

        self.__locate_config_files(file)
        self.__read_config()       

    def __locate_config_files(self, file=None):
        """Locate the configuration files to use"""

        # read the application default config file
        app_config_file = os.path.dirname(os.path.abspath(__file__)) + "/../.tt-config.json"
        if os.path.exists(app_config_file):
            config_files = [app_config_file]

        # add the default config file if it exists
        if os.path.exists(f"{self.get('workdir')}/{self.get('default_configfile')}"):
            config_files.append(f"{self.get('workdir')}/{self.get('default_configfile')}")

        # add the config file passed as input if it exists
        if file:
            if os.path.exists(file):
                config_files.append(file)
            else:
                print(f"ERROR: The config file '{file}' does not exist", file=sys.stderr)
                sys.exit(1)

        self.set('config_files', config_files)


    def __read_config(self):
        """Read the configuration file in order of priority"""
        
        complete=False
        # Get the git root directory and set the config file
        [git_root, result] = Gitter(
            cmd="git rev-parse --show-toplevel",
            msg="Get the git root directory").run()
        if not git_root or result.returncode != 0:
            print(f"Could not determine the git root directory", file=sys.stderr)
            sys.exit(1)


        # For each config file, read the json and set the properties, let each config file override the previous one
        for config_file in self.get('config_files'):
            if not os.path.exists(config_file):
                continue

            with open(config_file, 'r') as f:
                try:
                    # the config file is a json file but It may contain comments - lines beginning with '//' (may have whitespace before)
                    # so we need to remove them before parsing the json
                    # read the file and remove comments
                    lines = f.readlines()
                    lines = [line for line in lines if not re.match(r'^\s*//', line)]
                    # join the lines back together
                    config_data = ''.join(lines)
                    # parse the json
                    json_data = json.loads(config_data)
                    for key, value in json_data.items():
                        self.set(key, value)
                except json.JSONDecodeError as e:
                    print(f"Could not parse JSON from {config_file}: {e}", file=sys.stderr)
                    sys.exit(1)

        complete=True
        return complete