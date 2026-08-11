import json
import os

from rm_api import (
    API,
    get_file,
    get_file_contents,
    Metadata,
    update_root,
    put_file,
    File,
    make_hash,
    DocumentSyncProgress,
)
from slashr import SlashR

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

try:
    files = get_file(api, root["hash"], use_cache=False)
    print(f"Your current root file hash: {root['hash']}")
    print(f"Version {files._version} with {files.items} items")
    print(
        "Your root file is fine, press enter if you still want to try and find a replacement from cache"
    )
    input("> press enter")
except:
    print("Your root file is fucked!")

potential_roots = {}

for cache in os.listdir(api.sync_file_path):
    try:
        files = get_file(api, cache, use_cache=True)
    except:
        continue
    if any(map(lambda file: "." in file.uuid, files.files)):
        continue

    potential_roots[cache] = files.files

if len(potential_roots) == 0:
    print("No luck! Couldn't find any cached root files")
    exit()

print(
    f"Great luck! Found {len(potential_roots)} potential root files, sorting by last modified"
)

root_last_modified = {}

with SlashR() as sr:
    for i, (hash_of_root, files) in enumerate(potential_roots.items()):
        if len(files) == 0:
            continue
        sr.print(
            f"Checking {hash_of_root} {i + 1}/{len(potential_roots)} - ITEMS: {len(files)}"
        )
        last_modified = 0
        for file in files:
            try:
                file_root = get_file(api, file.hash, file.rm_filename, use_cache=True)
            except:
                continue
            for sub_file in file_root.files:
                if not sub_file.uuid.endswith(".metadata"):
                    continue
                try:
                    metadata_raw = get_file_contents(
                        api, sub_file.hash, sub_file.rm_filename, use_cache=True
                    )
                except:
                    continue

                metadata = Metadata(metadata_raw, sub_file.hash)
                last_modified = max(last_modified, int(metadata.last_modified))
        root_last_modified[hash_of_root] = last_modified

print("\nNEWEST FIRST, OLDEST LAST")
for hash_of_root, files in sorted(
    potential_roots.items(),
    key=lambda root: root_last_modified.get(root[0], 0),
    reverse=True,
):
    if len(files) == 0:
        continue
    last_modified = root_last_modified.get(hash_of_root, 0)
    print(f"{hash_of_root} - ITEMS: {len(files)}")

picked_root = input("\nType the hash of the root file you picked: ")

if picked_root not in potential_roots:
    print(
        "That hash seems wrong, run again and make sure to copy paste it with no spaces"
    )
    exit()

current_root = api.get_root()

files = potential_roots[picked_root]

contents = "3\n" + "\n".join(File.to_root_line(file) for file in files)
contents = contents.encode()

if (
    input("also upload this root file? (shouldn't need to) [y/N]")
    .lower()
    .startswith("y")
):
    file = File(make_hash(contents), f"root.docSchema", len(files), len(contents))
    p = DocumentSyncProgress(file.uuid)
    put_file(api, file, contents, p)
    print(f"Uploaded root file {p.done} / {p.total}")

new_root = {
    "broadcast": True,
    "generation": current_root["generation"],
    "hash": picked_root,
}
update_root(api, new_root)
