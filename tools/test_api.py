import json
import threading
import time

from slashr import SlashR
from rm_api import API, Document

with open('../config.json', 'r') as f:
    config = json.load(f)

api = API(uri=config['uri'], discovery_uri=config['discovery_uri'], token_file_path='../token', sync_file_path='../sync')
api.debug = True

with SlashR(False) as sr:
    items = 0
    last_update_time = 0
    done = 0


    def track_progress(items_done, items_total):
        global items, done, last_update_time
        items = items_total
        done = items_done
        last_update_time = time.time()


    threading.Thread(target=api.get_documents, args=(track_progress,), daemon=True).start()

    while last_update_time <= 0:
        pass
    while done < items:
        sr.print(f"Downloading documents... {done}/{items}")
    sr.print(f"Downloaded {items} documents")

meows = set()
for document in api.documents.values():
    meows.add(document.metadata.visible_name)

with open('../assets/data/light.pdf', 'rb') as f:
    light = f.read()

docs = []
for i in range(100):
    name = f"this is a very accurate test ;3 [{i}]"
    print(name)
    if name in meows:
        continue
    docs.append(Document.new_pdf(api, name, light, parent='debug'))

api.upload_many_documents(docs)
