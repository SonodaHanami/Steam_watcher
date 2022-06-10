import os
import json
from .utils import *

__all__ = [
    'steam',
]

default_config = {
    'ADMIN': '',
    'BOT': '',
    'STEAM_APIKEY': '',
    'ONE_LINE_MODE': False,
    'BKB_RECOMMENDED': False,
    'IMAGE_MODE_OPTIONS': ['ORIGINAL_PNG', 'BASE64_IMAGE', 'YOBOT_OUTPUT'],
    'IMAGE_MODE': 'BASE64_IMAGE',
}

config_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'config.json'
)
if not os.path.exists(config_path):
    dumpjson(default_config, config_path)
else:
    config = loadjson(config_path)
    for c in default_config:
        if config.get(c) is None:
            config[c] = default_config[c]
    dumpjson(config, config_path)

mkdir_if_not_exists(os.path.expanduser('~/.Steam_watcher'))
mkdir_if_not_exists(os.path.expanduser('~/.Steam_watcher/fonts'))
mkdir_if_not_exists(os.path.expanduser('~/.Steam_watcher/images'))
mkdir_if_not_exists(os.path.expanduser('~/.Steam_watcher/DOTA2_matches/'))

from .steam import Steam
