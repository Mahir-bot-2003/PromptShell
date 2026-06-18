import sys
import os

# ── Ensure the project root is on sys.path so relative imports work
# regardless of where the user runs this file from.
_this_file = os.path.abspath(__file__)          # .../app/main.py
_app_dir   = os.path.dirname(_this_file)        # .../app/
_root_dir  = os.path.dirname(_app_dir)          # .../codecrafters-shell-python/

if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
    
if sys.version_info < (3, 8):
    sys.stderr.write("Promptshell requires Python 3.8 or higher.\n")
    sys.exit(1)

from app.shell import run   # absolute import — always works now

def main():
    run()

if __name__ == "__main__":
    main()
