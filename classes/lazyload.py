import os
import sys

class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)

class Lazyload:
    """Base class for lazy loading properties"""
    
    def __init__(self):
        self.props = {}

    def set(self, key, value):
        """Some syntactic sugar to set the class properties
        
        Args:
            key (str): The key to set in the class properties
            value: The value to set the key to
        """
        self.props[key] = value
        return self.props[key]
    
    def get(self, key):
        """Some syntactic sugar to get the class properties
        
        Args:
            key (str): The key to get from the class properties - The key must exist in the class properties

        Returns:
            value: The value of the key in the class properties
        """    
        assert key in self.props, f"Property {key} not found on class"
        return self.props[key]
    
    async def load_prop(self, prop: str, cmd: str, msg: str):
        """
        Load a property and set the value on the properties
        """
        from gitter import Gitter

        [value, result] = await Gitter(
            cmd=f"{cmd}",
            msg=f"{msg}",
            die_on_error=True).run()
        self.set(prop, value)
        return value
    
