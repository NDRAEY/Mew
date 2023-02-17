import os
import sys
try:
    from log import Log as log
except ImportError:
    from .log import Log as log

class TargetManager:
    def __init__(self, target):
        module_dir = os.path.dirname(os.path.abspath(__file__))

        self.target_folder = module_dir + "/targets/" + target + "/"

        if not os.path.isdir(self.target_folder):
            log.error(f"Target `{target}` not found! ({self.target_folder})")
            exit(1)

    def get_file_contents(self, file):
        if not os.path.isfile(self.target_folder + file):
            log.error(f"File `{file}` not found in target `{self.target.split('/')[-1]}`")
            exit(1)
        
        with open(self.target_folder + file, "r") as f:
            data = f.read()
            f.close()
            return data
