import os
import sys
import json
import re
import asyncio


class Lazyload:
    """Base class for lazy loading properties"""

    _manifest_file = os.path.dirname(os.path.abspath(__file__)) + "/props.json"
    _manifest = {}  # Class-level variable to store loaded properties
    _manifest_loaded = False

    # Load the manifest file if it exists
    if os.path.exists(_manifest_file):
        with open(_manifest_file, 'r') as f:
            try:
                # Load "JSON with comments"
                lines = f.readlines()
                lines = [line for line in lines if not re.match(
                    r'^\s*//', line)]
                config_data = ''.join(lines)
                _manifest = json.loads(config_data)
                _manifest_loaded = True
            except json.JSONDecodeError as e:
                print(
                    f"ERROR: Could not parse JSON from {_manifest_file}: {e}", file=sys.stderr)
                sys.exit(1)

    def __init__(self):
        self.props = {}
        self._loaded = []  # List of manifest groups that have been loaded

    def set(self, key: str, value: str):
        """Setter for the class properties
        Args:
            key (str): The key to set in the class properties
            value: The value to set the key to
        """
        self.props[key] = value
        return self.props[key]

    def get(self, key: str):
        """Getter for the class properties
        Args:
            key (str): The key to get from the class properties.
        Returns:
            value: The value of the key in the class properties
        Raises:
            AssertionError: If the key is not found in the class properties
        """
        assert key in self.props, f"Property {key} not found on class"
        return self.props[key]
    
    def to_json(self, file: str = None) -> bool:
        """Prints out the 'props' dict as json
        Args:
            file (str): Optional file to write the output to. If not provided, prints to stdout.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            output = json.dumps(self.props, indent=4)
            if file:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file), exist_ok=True)
                with open(file, 'w') as f:
                    f.write(output)
            else:
                print(output)
            return True
        except Exception as e:
            print(f"ERROR: Could not write to file {file}: {e}", file=sys.stderr)
            return False



    async def _load_prop(self, prop: str, cmd: str, msg: str):
        """
        Load a property and set the value on the properties
        Args:
            prop (str): The property to set
            cmd (str): The command to run to get the value of the property
            msg (str): The message to print in verbose mode.
        Returns:
            value: The value of the property after running the command
        """
        from gitter import Gitter

        await Gitter.fetch()

        [value, _] = await Gitter(
            cmd=f"{cmd}",
            msg=f"{msg}",
            die_on_error=True).run()
        self.set(prop, value)
        return value

    async def _assert_props(self, props: list[str] ):
        """
        Assert that all properties in the list are loaded, and if no then initiate the load
        Args:
            props (list[str]): List of properties to assert
        Raises:
            AssertionError: If any of the properties are not loaded, and not defined in the manifest file
        """

        # Check if all properties are loaded
        for prop in props:
            if prop not in self.props or self.props[prop] is None:
                dep_group = self._get_manifest_group(self._caller(), prop)    
                await self._load_manifest(dep_group)

    def _caller(self):
        """Get the class name in lowercase to match the manifest"""
        return self.__class__.__name__.lower()
    
    async def _load_manifest(self, group: str = 'init'):
        """
        Load all properties from the manifest file relevant to the class instance.

        Args:
            group (str): The group of properties to load. 
            None implies group 'init'.

        Returns:
            true if properties were loaded, False otherwise.

        Raises:
            AssertionError: If the manifest file is not loaded or does not exist.
            AssertionError: If the class is not found in the manifest file.
        """
        # Check if the group is already loaded
        if group in self._loaded:
            return True

        # Require the manifest to be loaded
        assert self._manifest_loaded, f"ERROR: Manifest file '{self._manifest_file}' is not loaded or does not exist."

        caller = self._caller()
        assert caller in self._manifest, f"ERROR: Class '{caller}' is not found in manifest '{self._manifest_file}'"

        tasks = []
        for prop in self._manifest[caller]:
            # Skip properties that are not in the specified group
            if group != self._manifest[caller][prop].get('group', 'init'):
                continue

            # check if the property has explicit dependecies, that are not loaded yet
            dependency = self._manifest[caller][prop].get('dependency', 'init')
            if group != 'init' and dependency not in self._loaded:
                # load the dependency first
                await self._load_manifest(dependency)

            # Find occurrences of {.*} in text (e.g., {someprop} and replace them with the property values)
            # The regex uses negative lookbehind (?<!{) and negative lookahead (?!{) assertions to ensure 
            # that the curly braces are not part of a double curly brace sequence ({{ or }}). 
            # This effectively ignores {{tree}} while still matching {branch_name}, {merge_base}, {squeeze_message} etc.
            cmd = self._manifest[caller][prop].get('cmd')
            matches = re.findall(r'(?<!{)\{(?!{)(.*?)\}', cmd)
            for match in matches:
                # Enforce the rule: No command can expect value substitution for props within the same group
                dep_group = self._get_manifest_group(caller, match)
                assert group != dep_group, f"ERROR: Property '{prop}' in group '{group}' defined in {self._manifest_file} implicitly depends on property '{match}'. They both belong to the same dependency group '{group}'. Value substitution within the same group is not allowed."
                if dep_group not in self._loaded:
                    await self._load_manifest(dep_group)

            # When all dependencies are loaded compile the final command by replacing
            # the dependency values are replaced e.g., {someprop} -> self.get('someprop')
            
            for match in matches:
                cmd = cmd.replace(f"{{{match}}}", str(self.get(match)))

            # Find and expand occurrences of {{.*}} in text (e.g., {{tree}})  and replace them with just a single '{' '}' e.g. {tree}
            matches = re.findall(r'{{(.*?)}}', cmd)
            for match in matches:
                cmd = cmd.replace(f"{{{{{match}}}}}", f"{{{match}}}")
            
            msg = self._manifest[caller][prop].get('msg', '')

            # Append the coroutine to the list
            tasks.append(self._load_prop(
                prop,
                cmd,
                msg)
            )

        # Run all coroutines concurrently
        await asyncio.gather(*tasks)
        self._loaded.append(group)
        return True

    def _get_manifest_group(self, caller: str, prop: str):
        """Get the group of a property from the manifest file
        If the the property is not found in the manifest file, return 'init' as the default group.
        Args:
            caller (str): The class name in lowercase
            prop (str): The property to get the group for
        Returns:
            str: The group of the property
        """
        try:
            return self._manifest[caller][prop].get('group', 'init')
        except KeyError:
            return 'init'  # Default group if not found
   