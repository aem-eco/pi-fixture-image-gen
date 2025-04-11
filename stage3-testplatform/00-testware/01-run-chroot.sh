#!/usr/bin/bash -e

# Create python venv
# activation of the venv and installation of packages
/usr/bin/python3.11 -m venv "/home/prod/${PY_VENV_NAME}"
source "/home/prod/pyVenv/bin/activate"
pip install pip --upgrade --no-input
pip install cython --no-input
pip install gpiod --no-input
pip install pyinstrument --no-input
pip install pyserial --no-input
pip install regex --no-input
pip install requests --no-input
pip install termcolor --no-input
deactivate