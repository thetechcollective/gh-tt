import os
import sys
import subprocess

# Add directory of this class to the general class_path
# to allow import of sibling classes
class_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(class_path)


def run(cmd=str, die_on_error=True, msg=None, verbose=False, workdir=None):
    """Run a shell command and return the output and result"""

    if workdir == None:
        workdir = os.getcwd()
        
    if verbose:
        if msg != None:
            vmsg = f"# {msg}:\n"
        else:
            vmsg = ""        
        print(f"{vmsg}$ {cmd}\n")
    
    result = subprocess.run(
        cmd, capture_output=True, text=True, shell=True, cwd=workdir)
    if die_on_error and not result.returncode == 0:
        raise RuntimeError(f"{result.stderr}")
        sys.exit(1)
    output = result.stdout.strip()
    return output, result