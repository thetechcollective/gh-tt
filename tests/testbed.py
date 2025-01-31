import os
import subprocess


class Testbed:
    @staticmethod
    def cleanup_testbed(test_dir):
        if os.path.exists(test_dir):
            print("Cleaning up the testbed for reuse")
            try:
                subprocess.check_call('rm -rf {}'.format(test_dir), shell=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to remove test directory: {e}")            
        
    @staticmethod
    def create_testbed(test_dir):
        Testbed.cleanup_testbed(test_dir)
        try:
            subprocess.check_call('mkdir -p {}'.format(test_dir), shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to create test directory: {e}")
        
        try:
            subprocess.check_call('git init', cwd=test_dir, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to initialize git repository: {e}")
        
        try:
            subprocess.check_call('git checkout -b testbed', cwd=test_dir, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to create test branch: {e}")


    @staticmethod
    def run_cli(cli_path, *args, cwd):
        result = subprocess.run(
            [cli_path] + list(args), cwd=cwd, capture_output=True, text=True)
        return result
    
    @staticmethod
    def git_dataset_1(test_dir):
        subprocess.check_call('echo "testfile">testfile.txt', cwd=test_dir, shell=True)
        subprocess.check_call('git add testfile.txt', cwd=test_dir, shell=True)
        subprocess.check_call('git commit -m "added testfile"', cwd=test_dir, shell=True)
        subprocess.check_call('git tag -a -m zerozeroone v0.0.1', cwd=test_dir, shell=True)
        subprocess.check_call('git tag -a -m onetwoone ver1.2.1', cwd=test_dir, shell=True)
        subprocess.check_call('git tag -a -m oneoneone version1.1.1', cwd=test_dir, shell=True)
        subprocess.check_call('git tag -a -m twooneone version2.1.1-freetext', cwd=test_dir, shell=True)
        subprocess.check_call('git tag -a -m nonvalid version3.11-freetext', cwd=test_dir, shell=True)
