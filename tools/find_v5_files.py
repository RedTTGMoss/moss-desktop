import json
import os
import shutil

from slashr import SlashR

from rm_api import API, get_file, get_file_contents
from rm_lines.rmscene import HEADER_V6

DIR = 'v5_export'

if os.path.exists(DIR):
    shutil.rmtree(DIR)

os.makedirs(DIR, exist_ok=True)

with open('../config.json', 'r') as f:
    config = json.load(f)

api = API(uri=config['uri'], discovery_uri=config['discovery_uri'], token_file_path='../token', sync_file_path='../sync')
api.debug = True
api.ignore_error_protection = True

root = api.get_root()

_, files = get_file(api, root['hash'])

with SlashR() as sr:
    for i, file in enumerate(files):
        _, sub_files = get_file(api, file.hash)
        for j, sub_file in enumerate(sub_files):
            if not sub_file.uuid.endswith('.rm'):
                sr.print(f"Skipping {sub_file.uuid} {j + 1}/{len(sub_files)} [{i + 1}/{len(files)}]")
                continue
            else:
                sr.print(f"Downloading {sub_file.uuid} {j + 1}/{len(sub_files)} [{i + 1}/{len(files)}]")
            data = get_file_contents(api, sub_file.hash, True)
            header = data[0:len(HEADER_V6)]
            if header != HEADER_V6:
                with open(os.path.join(DIR, sub_file.uuid.split('/')[-1]), 'wb') as f:
                    f.write(data)

print("Exported v5 lines files to v5_export directory")
