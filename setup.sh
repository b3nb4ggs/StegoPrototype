!#/bin/bash

python3 -m pip install --upgrade pip
python3 -m venv stego_env
source stego_env/bin/activate
python3 -m pip install -r requirements.txt