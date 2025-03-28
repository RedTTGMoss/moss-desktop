import json
import os
import shutil
import threading
import time

import humanize
from slashr import SlashR

from gui.sync_stages import SYNC_STAGE_TEXTS
from rm_api import API, FileSyncProgress

DIR = 'root_export'


class Wait:
    def __init__(self):
        self.finished = False

    def finish(self):
        self.finished = True


def get_download_info(api_used):
    done = 0
    total = 0
    for download_operation in api_used.download_operations:
        done += download_operation.done
        total += download_operation.total
    if done and total and done < total:
        return f"Downloaded {humanize.naturalsize(done)} / {humanize.naturalsize(total)}"
    return ""


def keep_track(progress: FileSyncProgress):
    with SlashR() as sr:
        while not progress.finished:
            sr.print(
                f"{SYNC_STAGE_TEXTS[progress.stage]} {progress.done} / {progress.total}")
            time.sleep(0.1)


def hook(event):
    if isinstance(event, FileSyncProgress):
        threading.Thread(target=keep_track, args=(event,)).start()


if os.path.exists(DIR):
    shutil.rmtree(DIR)

with open('config.json', 'r') as f:
    config = json.load(f)

api = API(uri=config['uri'], discovery_uri=config['discovery_uri'])
api2 = API(token_file_path='token2', log_file='2' + api.log_file)
api.debug = True
api2.debug = True

api.get_documents()
api2.add_hook('hook', hook)

with SlashR() as sr:
    for i, document in enumerate(api.documents.values()):
        try:
            wait = Wait()
            document.ensure_download_and_callback(wait.finish)
            while not wait.finished:
                sr.print(
                    f"Downloading document {document.metadata.visible_name} {i + 1}/{len(api.documents)} {get_download_info(api)}")
        except KeyboardInterrupt:
            api.force_stop_all()
            exit()

print("Uploading...")
api2.upload_many_documents(list(api.documents.values()) + list(api.document_collections.values()), unload=True)
