import json
from pprint import pprint
from pygameextra import settings
from box import Box

with open('../config.json', 'r') as f:
    config = Box(json.load(f))

class gc:
    config = config

class doc:
    class metadata:
        visible_name = 'test'

setattr(settings, 'game_context', gc)
setattr(settings, 'config_file_path', 'config.json')
setattr(settings, 'config', config)

from gui import file_prompts as fp

def callback(data):
    pprint(data)

fp.import_prompt(callback)
fp.import_debug(callback)
fp.notebook_prompt(callback)
fp.export_prompt(doc, callback)