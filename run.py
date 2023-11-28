import os
import subprocess

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to PIP_Manager.py
pip_manager_path = os.path.join(script_dir, 'src', 'PIP_Manager.py')

# Run PIP_Manager.py using subprocess
subprocess.run(['python', pip_manager_path])
