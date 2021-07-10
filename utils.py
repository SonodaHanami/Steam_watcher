import os
import json


def loadjson(jsonfile, default={}):
    try:
        data = json.load(open(jsonfile, 'r', encoding='utf-8'))
    except:
        data = default
    finally:
        return data

def dumpjson(jsondata, jsonfile):
    with open(jsonfile, 'w', encoding='utf-8') as f:
        json.dump(jsondata, f, ensure_ascii=False, indent=4)

def load_config():
    return loadjson(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.json'))

def mkdir_if_not_exists(path):
    if not os.path.exists(path):
        os.mkdir(path)