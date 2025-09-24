TA2LSM, 23.09.2025
HTML Link Parser and Downloader

* Adding python to PATH

- macOS    : add .zshrc file to this -> export PATH="/opt/homebrew/bin/bin:$PATH"
- windows  : Environment variables -> PATH add pyhton and python\Scripts

OS restart may needed to proper PATH detection.

* run.py

run.py will create virtual environment and install dependencies defined in "requirements.txt".
No need to execute pip install -r requirements.txt command.

- macOS    : Storage -> Users -> Your username -> venvs -> project name
- windows  :

* After build script error may occur

- macOS
chmod +x download
./download

- windows
...

* For executing
- macOS    : go to dist folder and execute ./main 