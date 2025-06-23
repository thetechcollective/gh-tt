
import os
import sys

# Add directory of this class to the general class_path
# to allow import of sibling classes

class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)