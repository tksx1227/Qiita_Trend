import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)

# dotenv_path = join(dirname(__file__), '.env')
# load_dotenv(dotenv_path)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
USER_ID = os.environ.get("USER_ID")

QIITA_USER_NAME = os.environ.get("QIITA_USER_NAME")
QIITA_PASSWORD = os.environ.get("QIITA_PASSWORD")
