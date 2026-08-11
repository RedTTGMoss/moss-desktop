import json
import os
import shutil

from rm_api import API, get_file, get_file_contents
from slashr import SlashR

DIR = "root_export"

if os.path.exists(DIR):
    shutil.rmtree(DIR)

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

files = get_file(api, root["hash"])

names = {}

with SlashR() as sr:
    for i, file in enumerate(files.files):
        file_dir = os.path.join(DIR, file.uuid)
        os.makedirs(file_dir, exist_ok=True)
        sub_files = get_file(api, file.hash)
        for j, sub_file in enumerate(sub_files.files):
            sr.print(
                f"Downloading {sub_file.uuid} {j + 1}/{sub_files.items} [{i + 1}/{files.items}]]"
            )
            with open(os.path.join(file_dir, sub_file.uuid), "wb") as f:
                f.write(data := get_file_contents(api, sub_file.hash, True))
            if sub_file.uuid.endswith(".metadata"):
                metadata = json.loads(data.decode())
                if name := metadata.get("visibleName"):
                    names[file.uuid] = name
print("Exported root files to root_export directory")
for file in files.files:
    print(f'{file.uuid}[{file.content_count}] -> "{names.get(file.uuid, "")}"')
