import os
import sys
import subprocess as sp
import yaml

try:
    from log import Log as log
except ImportError:
    from .log import Log as log

class TargetManager:
    def __init__(self, target):
        module_dir = os.path.dirname(os.path.abspath(__file__))

        self.mod_folder = module_dir + "/targets/"
        self.target_folder = self.mod_folder + target + "/"
        self.target_file   = self.mod_folder + target + ".yml"

        if not os.path.isdir(self.target_folder):
            log.error(f"Target `{target}` not found! ({self.target_folder})")
            exit(1)

        with open(self.target_file, "r") as f:
            self.config = yaml.load(f.read(), Loader=yaml.Loader)

    def get_file_contents(self, file):
        if not os.path.isfile(self.target_folder + file):
            log.error(f"File `{file}` not found in target `{self.target.split('/')[-1]}`")
            exit(1)
        
        with open(self.target_folder + file, "r") as f:
            data = f.read()
            f.close()
            return data

    def full_path(self, file):
        return self.target_folder+"/"+file
