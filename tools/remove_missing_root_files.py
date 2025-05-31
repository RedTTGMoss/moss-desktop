import json

import colorama
from colorama import Fore
from slashr import SlashR

from rm_api import API, get_file, put_file, File, update_root, DocumentSyncProgress, check_file_exists, Metadata, \
    get_file_contents

colorama.init()

with SlashR(False) as sr:
    sr.print(f"{Fore.BLUE}Loading configuration...{Fore.RESET}")
    with open('../config.json', 'r') as f:
        config = json.load(f)

    sr.print(f"{Fore.BLUE}Logging in using the API{Fore.RESET}")
    api = API(uri=config['uri'], discovery_uri=config['discovery_uri'], token_file_path='../token', sync_file_path='../sync')
    api.debug = True
    api.ignore_error_protection = True

    sr.print(f"{Fore.YELLOW}Hold on, fetching documents using the API{Fore.RESET}")
    api.get_documents()
    print(f"{Fore.LIGHTBLACK_EX}Current root hash: {api.last_root}{Fore.RESET}")
    sr.print(
        f"{Fore.GREEN}Got {len(api.documents)} Documents and "
        f"{len(api.document_collections)} Document Collections{Fore.RESET}")

_, files = get_file(api, api.last_root)
file_uuids = (
        [document.uuid for document in api.documents.values()] +
        [document_collection.uuid for document_collection in api.document_collections.values()]
)

with SlashR(False) as sr:
    files_invalid = 0
    valid_files = []
    invalid_files = []
    for i, file in enumerate(files):
        sr.print(
            f'{Fore.CYAN}Checking {i + 1} of {len(files)} '
            f'{Fore.GREEN}valid: {len(valid_files)} '
            f'{Fore.RED}invalid: {len(invalid_files)}{Fore.RESET}'
        )
        if file.uuid in file_uuids:
            valid_files.append(file)
        else:
            invalid_files.append(file)

    sr.print(
        f'{Fore.CYAN}Checked {len(files)} items on your cloud. '
        f'{Fore.GREEN}valid: {len(valid_files)} '
        f'{Fore.RED}invalid: {len(invalid_files)}{Fore.RESET}'
    )

for invalid_file in invalid_files:
    _, sub_files = get_file(api, invalid_file.hash)
    missing_extensions = set()
    available_extensions = set()
    files_ok = 0
    metadata = None
    for sub_file in sub_files:
        extension = sub_file.uuid.rsplit('.', 1)[-1]
        if check_file_exists(api, sub_file.hash, use_cache=False):
            files_ok += 1
            available_extensions.add(extension)
            if not sub_file.uuid.endswith('.metadata'):
                continue
            raw_metadata = get_file_contents(api, sub_file.hash)
            metadata = Metadata(raw_metadata, sub_file.hash)
        else:
            missing_extensions.add(extension)
    print(
        f'{metadata.visible_name if metadata else f"{Fore.LIGHTBLACK_EX}MISSING METADATA"} '
        f'{Fore.MAGENTA}Files: {files_ok} / {len(sub_files)} '
        f'{Fore.GREEN}Available extensions: {list(available_extensions)} '
        f'{Fore.YELLOW}Missing extensions: {list(missing_extensions)} '
        f'{Fore.BLUE}{invalid_file.hash}{Fore.RESET}'
    )

if len(invalid_files) == 0:
    print(f"{Fore.GREEN}Looks like everything is clean!{Fore.RESET}")
    exit()

input("Press enter to upload this new data")

root_sync_operation = DocumentSyncProgress('root')
root_file_contents, root_file = File.create_root_file(valid_files)

put_file(api, root_file, root_file_contents, root_sync_operation)

root = api.get_root()
update_root(api, {
    "broadcast": True,
    "generation": root['generation'],
    "hash": root_file.hash
})

print(f"Updated root hash: {root_file.hash}")
