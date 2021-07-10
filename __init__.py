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
}

config_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'config.json'
)
if not os.path.exists(config_path):
    dumpjson(default_config, config_path)

mkdir_if_not_exists(os.path.expanduser('~/.Steam_watcher'))
mkdir_if_not_exists(os.path.expanduser('~/.Steam_watcher/fonts'))
mkdir_if_not_exists(os.path.expanduser('~/.Steam_watcher/images'))

from .steam import Steam
