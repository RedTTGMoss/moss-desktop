import json
import os
import shutil

from rm_api import API, get_file, get_file_contents, ROOT_DOC_SCHEMA
from rm_lines.rmscene import HEADER_V6
from slashr import SlashR

DIR = "v5_export"

if os.path.exists(DIR):
    shutil.rmtree(DIR)

os.makedirs(DIR, exist_ok=True)

with open("../config.json", "r") as f:
    config = json.load(f)

api = API(
    uri=config["uri"],
    discovery_uri=config["discovery_uri"],
    token_file_path="../token",
    sync_file_path="../sync.old",
)
api.debug = True
api.ignore_error_protection = True

root = api.get_root()

files = get_file(api, root["hash"], ROOT_DOC_SCHEMA)

with SlashR() as sr:
    for i, file in enumerate(files.files):
        sub_files = get_file(api, file.hash, file.rm_filename)
        for j, sub_file in enumerate(sub_files.files):
            if not sub_file.uuid.endswith(".rm"):
                sr.print(
                    f"Skipping {sub_file.uuid} {j + 1}/{sub_files.items} [{i + 1}/{files.items}]"
                )
                continue
            else:
                sr.print(
                    f"Downloading {sub_file.uuid} {j + 1}/{sub_files.items} [{i + 1}/{files.items}]"
                )
            data = get_file_contents(api, sub_file.hash, True)
            header = data[0 : len(HEADER_V6)]
            if header != HEADER_V6:
                with open(os.path.join(DIR, sub_file.uuid.split("/")[-1]), "wb") as f:
                    f.write(data)

print("Exported v5 lines files to v5_export directory")
