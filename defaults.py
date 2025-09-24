import os, sys

PROJECT_NAME = "Downloader"
REQ_FILE = "requirements.txt"
DEBUG = True

# Derlenmiş exe çalışıyorsa exe'nin dizini, değilse script'in dizini
# BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
DIST_DIR = os.path.join(os.getcwd(), "dist")
CHROMIUM_DIR = os.path.join(DIST_DIR, "chromium")
DRIVER_DIR = os.path.join(DIST_DIR, "driver")

CHROMIUM_API_VERSIONS = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
CHROMIUM_API_WITH_DOWNLOADS = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
CHROMEDRIVER_STORAGE = "https://chromedriver.storage.googleapis.com"

DEFAULT_CHUNK_SIZE = 1024*1024  # 1 MB
DEFAULT_CHROME_DRIVER_MIN_SIZE = 5242880
DEFAULT_CHROMIUM_MIN_SIZE = 20971520

DEFAULT_TIME_BEFORE_PAGE_LOAD = 5

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform.startswith("darwin")

# ----------------------------
# Folders
# ----------------------------
# cwd = os.getcwd()

# if IS_WINDOWS:
#     chromedriver_path = os.path.join(cwd, "chromedriver.exe")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-win", "chrome.exe")
# elif IS_MAC:
#     chromedriver_path = os.path.join(cwd, "chromedriver_mac")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-mac", "Chromium.app/Contents/MacOS/Chromium")
# elif IS_LINUX:
#     chromedriver_path = os.path.join(cwd, "chromedriver_linux")
#     chromium_dir = os.path.join(cwd, "chromium")
#     chromium_path = os.path.join(chromium_dir, "chrome-linux", "chrome")

# if IS_WINDOWS:
#   try:
#       import win32api
#   except ImportError:
#       win32api = None