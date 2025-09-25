# HTML Link Parser and Downloader
Author: TA2LSM (23.09.2025)

This project gets URL as an input and downloads it. After that parses html file for

```html
<a href="...">link</a>
```

then download every link in that html file to user's desktop. Undetected Chromedriver, Chromium and ChromeDriver used for this purpose.

## Adding python to PATH
If you couldn't succeed to adding python to path by python setup. Do it manually :

+ **macOS** : add .zshrc file to this -> export PATH="/opt/homebrew/bin/bin:$PATH" (if python installed with homebrew)
Otherwise, in terminal "which python" command gives you absolute path of your python packages.

+ **Windows** : Find (Environment variables -> PATH) then add Pyhton and Python\Scripts to path. For Example: 

```
C:\Users\<username>\AppData\Local\Programs\Python\Python313\
C:\Users\<username>\AppData\Local\Programs\Python\Python313\Scripts\)
```

OS restart may needed after that to proper PATH detection.

## Python Package
Some differences in the command lines like :

+ **macOS** : python3 main.py
+ **Windows** : python main.py

## How to Build
In terminal go to project root and

+ **macOS** :
```
python3 build.py
```

+ **Windows** :
```
python build.py
```

***build.py*** will create virtual environment and install dependencies defined in "requirements.txt". No need to execute this:

```
pip install -r requirements.txt
```

**venv** folder will be generated in the project root.

## Script Execution
After build, error may occur about script execution. OS permissions needed to be changed.

+ **macOS** in the same directory with the builded code (build folder) :
```
chmod +x download    <- make it executable
./download           <- run
```

+ **Windows** (enable scripts)
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```
OR 
```
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser
```

## For executing
After build
+ **macOS** : go to "dist" folder and execute ./Downloader 
+ **Windows** : go to "dist" folder and double click Downloader.exe

## Enable Virtual Environment
This may need to test some modules by itselves. Without build some libraries may not be installed in the venv. Activate virtual environment :

+ **macOS**:
```python
source venv/bin/activate
```

+ **Windows**:
```python
cmd (windows terminal): venv\Scripts\activate.bat
powershell (VSCode terminal): .\venv\Scripts\Activate.ps1
```

After this you should be in the venv. In terminal you should see :
```
(venv) PS C:\...\...
```

* Upgrade pip and install dependencies if necessary in the **venv**:
```python
pip install --upgrade pip
pip list -> check installed packages
```

* You can install necessary packages by yourself if you want :
```python
pip install requests selenium 
```

* Install project dependencies defined in the ***"requirements.txt"*** :
```python
macOS: python3 build.py
Windows: python build.py
```
## Testing modules
If all dependencies are installed correctly you can make self testing main.py :
```python
macOS: python3 main.py
Windows: python main.py
```

## Selecting Driver 
In defaults.py you can change driver method :
```
USE_UC_BROWSER = True -> Undetected Chrome Driver
USE_UC_BROWSER = False -> Selenium
```
After changing driver method, you may delete "chromium" and "driver" folders under "dist" folder before you run this code. Version compabilities could be a problem and packages needs to be downloaded from zero.