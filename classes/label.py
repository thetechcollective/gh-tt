from project import Project
from lazyload import Lazyload
from config import Config
from gitter import Gitter
import os
import subprocess
import sys
import re
import json
import asyncio

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


class Label(Lazyload):
    """Class used to represent a GitHub issue - in context of the current development branch"""

    _all = {}
    _loaded=False

    def __init__(self, name:str, create:bool=False):
        super().__init__()

        self.set('name', name)

        if not Label._loaded:
            self._reload()

        found = False
        for label in Label._all:
            if label['name'] == name:
                self.props = label
                found = True
                break
        
        if not found:
            if create:
                try:
                    config = Config()._config_dict
                    color = config['labels'][name]['color']
                    description = config['labels'][name]['description']
                except KeyError as e:
                    print(f"ERROR: Label '{name}' not defined in the config file", file=sys.stderr)
                    sys.exit(1)

                self.props = self.create_new(name=name, description=description, color=color, force=True).props
            else:                
                print(f"ERROR: Label '{name}' doesn't exist in current git context", file=sys.stderr)
                sys.exit(1)


    @classmethod
    def create_new(cls, name=str, description:str=None, color:str=None, force:bool=False):
        """Create a new label in the current repository
        Works as an alternative to the constructor, call it on the class and it will return a new Label object

        Args:
            name (str): The name of the label (required)
            description (str): The description of the label
            color: The color of the label (defaults to an auto generated arbitrary color)
            force: Update color and description if the label already exist (invalid if description or color is None, defaults to False)
        """

        description_switch = f" --description '{description}'" if description is not None else ''
        color_switch = f" --color {color}" if color is not None else ''
        force_switch = ' --force' if force and description is not None and color is not None else ''

        [output, result] = asyncio.run(Gitter(
            cmd=f"gh label create '{name}'{description_switch}{color_switch}{force_switch}",
            msg="Create a new lable").run()
        )
        cls._loaded = False
        return cls(name=name)
    
    @classmethod
    def validate(cls, name: str, category: str) -> bool:
        config = Config().config()
        
        is_valid = False
        for label_name, label_data in config["labels"].items():
            if label_data["category"] == category and label_name == name:
                is_valid = True
                break

        if not is_valid:
            valid_labels = [label_name for label_name, label_data in Config()._config_dict['labels'].items() if label_data["category"] == category]
            print(f"🛑  ERROR: \"{name}\" passed in --type is not matching any label with category '{category}' defined in the config. Choose one of the labels defined: {valid_labels}")
            sys.exit(1)

    
    
    
    def _reload(cls):
        """Reload the labels from the current repository"""
        list_all =  asyncio.run(cls._run('json_list_all'))
        try:
            Label._all = json.loads(list_all)                
        except ValueError as e:
            pass
            print(
                f"ERROR: Could not parse the json", file=sys.stderr)
            sys.exit(1)
        
        Label._loaded = True


