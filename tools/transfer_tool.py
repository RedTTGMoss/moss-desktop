import json
import os
import shutil
import threading
import time

import humanize
from rm_api import API, FileSyncProgress, DEFAULT_REMARKABLE_URI, DEFAULT_REMARKABLE_DISCOVERY_URI, \
    DocumentSyncProgress, Document
from slashr import SlashR

from gui.sync_stages import SYNC_STAGE_TEXTS

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


document_sync_progress = []


def keep_track(progress: FileSyncProgress):
    with SlashR() as sr:
        while not progress.finished:
            progresses = list(filter(lambda prog: not prog.finished, document_sync_progress))
            done = sum(map(lambda prog: prog.done, progresses))
            total = sum(map(lambda prog: prog.total, progresses))
            if done < total:
                sr.print(
                    f"{SYNC_STAGE_TEXTS[progress.stage]} {progress.done} / {progress.total} - "
                    f"{humanize.naturalsize(done)} / {humanize.naturalsize(total)}"
                )
            else:
                sr.print(
                    f"{SYNC_STAGE_TEXTS[progress.stage]} {progress.done} / {progress.total}")
            time.sleep(0.1)


def hook(event):
    if isinstance(event, FileSyncProgress):
        threading.Thread(target=keep_track, args=(event,)).start()
    elif isinstance(event, DocumentSyncProgress):
        document_sync_progress.append(event)


if os.path.exists(DIR):
    shutil.rmtree(DIR)

with open('../config.json', 'r') as f:
    config = json.load(f)

api = API(uri=config['uri'], discovery_uri=config['discovery_uri'], token_file_path='../token',
          sync_file_path='../sync')

upload_uri = config.get('upload_uri')
if not upload_uri:
    upload_uri = input("Enter the URI of the account you want to upload to: ")

api2 = API(uri=upload_uri,
           discovery_uri=DEFAULT_REMARKABLE_DISCOVERY_URI if upload_uri == DEFAULT_REMARKABLE_URI else upload_uri,
           token_file_path='../token2', log_file='2' + api.log_file, sync_file_path='../sync')
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

print(api.uri, "->", api2.uri)
input("Confirm?")

files = list(api.documents.values()) + list(api.document_collections.values())

if input("Limit 100mb uploads for cloudflare? [Y,n]").lower()[0] != 'n':
    for file in files:
        if isinstance(file, Document):
            if file.content.size_in_bytes >= 1e+8:
                print(f"Document {file.metadata.visible_name} is larger than 100mb, skipping upload")
                files.remove(file)

api2.upload_many_documents(files, unload=True)
